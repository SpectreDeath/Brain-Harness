"""Async event bus with append-only log.

The EventBus is the observability backbone of the harness. Every plugin
lifecycle change, tool invocation, and LLM call fires an event into the
bus. Handlers subscribe by event type and receive events asynchronously.

The event log is append-only — events are never mutated or deleted.
"""

from __future__ import annotations

import asyncio
import inspect
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from datetime import datetime
from pathlib import Path
from typing import Any, Generic, TypeVar

import structlog

from harness.kernel.context import ServiceKey
from .types import EventType, HarnessEvent

T = TypeVar("T")

logger = structlog.get_logger()

# Canonical service key for event bus
EVENT_BUS_KEY: ServiceKey[EventBus] = ServiceKey("events.bus")

# Type alias for event handlers
EventHandler = Callable[[HarnessEvent], Awaitable[None]]


class EventBus:
    """Async pub/sub event bus with append-only event log.

    Features:
        - Subscribe to specific event types or all events (``*``)
        - Append-only in-memory log (bounded deque)
        - Optional file persistence (JSONL format)
        - Async handler execution with error isolation

    Usage::

        bus = EventBus()
        bus.on(EventType.PLUGIN_ENABLED, my_handler)
        await bus.emit(plugin_event(EventType.PLUGIN_ENABLED, "my-plugin"))
    """

    def __init__(
        self,
        max_log_size: int = 10_000,
        log_file: Path | None = None,
    ) -> None:
        """Initialize the event bus.

        Args:
            max_log_size: Maximum number of events to keep in memory.
            log_file: Optional path to persist events as JSONL.
        """
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._log: deque[HarnessEvent] = deque(maxlen=max_log_size)
        self._log_file = log_file
        self._log_file_handle: Any = None

        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)

    async def emit(self, event: HarnessEvent) -> None:
        """Emit an event to all subscribed handlers.

        The event is appended to the log before handlers are called.
        Handler errors are logged but do not propagate — one bad handler
        cannot break the system.

        Args:
            event: The event to emit.
        """
        # Append to log first (append-only)
        self._log.append(event)

        # Persist to file if configured
        if self._log_file:
            await self._persist_event(event)

        # Collect matching handlers
        handlers: list[EventHandler] = []
        handlers.extend(self._handlers.get(event.event_type.value, []))
        handlers.extend(self._handlers.get("*", []))

        # Fire all handlers concurrently, isolating errors
        if handlers:
            results = await asyncio.gather(
                *(self._safe_call(h, event) for h in handlers),
                return_exceptions=True,
            )
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(
                        "Event handler error",
                        event_type=event.event_type.value,
                        handler=handlers[i].__name__,
                        error=str(result),
                    )

    def emit_sync(self, event: HarnessEvent) -> None:
        """Emit an event synchronously to the log and schedule async handlers.

        Appends the event to the append-only ledger immediately and persists to disk.
        If an active asyncio event loop is running, schedules handlers in the background.
        """
        self._log.append(event)

        if self._log_file:
            try:
                line = event.model_dump_json() + "\n"
                with open(self._log_file, "a", encoding="utf-8") as f:
                    f.write(line)
            except OSError as e:
                logger.warning("Failed to persist event", error=str(e))

        handlers: list[EventHandler] = []
        handlers.extend(self._handlers.get(event.event_type.value, []))
        handlers.extend(self._handlers.get("*", []))

        if handlers:
            try:
                loop = asyncio.get_running_loop()
                for h in handlers:
                    loop.create_task(self._safe_call(h, event))
            except RuntimeError:
                pass

    def fire(self, event: HarnessEvent) -> None:
        """Emit an event synchronously to the log and schedule async handlers.

        Canonical context-aware emission seam: appends to the log immediately and persists to disk.
        If an active asyncio event loop is running, schedules handlers in the background.
        """
        self.emit_sync(event)

    def on(
        self,
        event_type: EventType | str,
        handler: EventHandler,
    ) -> None:
        """Subscribe a handler to an event type.

        Args:
            event_type: The event type to subscribe to, or ``"*"`` for all events.
            handler: Async callable that receives the event.
        """
        key = event_type.value if isinstance(event_type, EventType) else event_type
        self._handlers[key].append(handler)
        logger.debug(
            "Event handler registered",
            event_type=key,
            handler=handler.__name__,
        )

    subscribe = on

    def off(self, handler: EventHandler) -> None:
        """Unsubscribe a handler from all event types.

        Args:
            handler: The handler to remove.
        """
        for key, handler_list in self._handlers.items():
            self._handlers[key] = [h for h in handler_list if h is not handler]

    def on_all(self, handler: EventHandler) -> None:
        """Subscribe a handler to ALL event types.

        Shortcut for ``bus.on("*", handler)``.
        """
        self.on("*", handler)

    @property
    def log(self) -> list[HarnessEvent]:
        """Return a copy of the event log (most recent events)."""
        return list(self._log)

    def log_since(self, after_id: str | None = None) -> list[HarnessEvent]:
        """Return events emitted after a given event ID.

        Args:
            after_id: Event ID to start after. If None, returns all events.
        """
        if after_id is None:
            return list(self._log)

        found = False
        result: list[HarnessEvent] = []
        for event in self._log:
            if found:
                result.append(event)
            elif event.id == after_id:
                found = True

        return result

    def filter_log(
        self,
        event_type: EventType | None = None,
        source: str | None = None,
        limit: int | None = None,
    ) -> list[HarnessEvent]:
        """Filter the event log by type and/or source.

        Args:
            event_type: Filter by event type.
            source: Filter by source plugin.
            limit: Maximum number of events to return.
        """
        result: list[HarnessEvent] = []
        for event in reversed(self._log):
            if event_type and event.event_type != event_type:
                continue
            if source and event.source != source:
                continue
            result.append(event)
            if limit and len(result) >= limit:
                break

        result.reverse()
        return result

    async def stream(
        self,
        event_type: EventType | str | None = None,
        source: str | None = None,
        *,
        since_id: str | None = None,
        replay_history: bool = True,
        queue_size: int = 1000,
    ) -> AsyncIterator[HarnessEvent]:
        """Stream events asynchronously as they are emitted to the bus.

        Supports optional historical event replay before streaming live events.
        Automatically cleans up the subscription queue when generator exits or cancels.

        Args:
            event_type: Optional event type filter (enum or string value).
            source: Optional source plugin filter.
            since_id: Optional event ID to start replaying history from.
            replay_history: Whether to yield matching past events from the log first.
            queue_size: Backlog queue capacity for the live stream.

        Yields:
            HarnessEvent instances in chronological order.
        """
        queue: asyncio.Queue[HarnessEvent] = asyncio.Queue(maxsize=queue_size)
        target_type_val: str | None = None
        if event_type is not None:
            target_type_val = (
                event_type.value if isinstance(event_type, EventType) else str(event_type)
            )

        async def _stream_handler(event: HarnessEvent) -> None:
            if target_type_val is not None and event.event_type.value != target_type_val:
                return
            if source is not None and event.source != source:
                return
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("Event stream queue full, dropping event", event_id=event.id)

        # Register live handler
        sub_key = target_type_val if target_type_val is not None else "*"
        self.on(sub_key, _stream_handler)

        try:
            # Replay historical events if requested
            if replay_history:
                history = self.log_since(since_id) if since_id else self.log
                for h_event in history:
                    if target_type_val is not None and h_event.event_type.value != target_type_val:
                        continue
                    if source is not None and h_event.source != source:
                        continue
                    yield h_event

            # Yield live stream
            while True:
                live_event = await queue.get()
                yield live_event
        finally:
            self.off(_stream_handler)

    @classmethod
    def iter_log_file(
        cls,
        path: Path | str,
        *,
        event_type: EventType | str | None = None,
        source: str | None = None,
        limit: int | None = None,
        since_id: str | None = None,
    ) -> Iterator[HarnessEvent]:
        """Lazily read and yield events from a persistent JSONL log file line-by-line.

        Zero memory bloat — parses events lazily without loading the full file into memory.

        Args:
            path: Path to the JSONL log file.
            event_type: Optional event type filter (enum or string value).
            source: Optional source plugin filter.
            limit: Maximum number of recent events to return.
            since_id: Event ID to start after.

        Yields:
            Parsed and filtered HarnessEvent instances.
        """
        p = Path(path)
        if not p.exists() or not p.is_file():
            return

        target_type_val: str | None = None
        if event_type is not None:
            target_type_val = (
                event_type.value if isinstance(event_type, EventType) else str(event_type)
            )

        if limit is not None and limit > 0:
            # When a tail limit is requested on a file, read into a bounded deque
            dq: deque[HarnessEvent] = deque(maxlen=limit)
            found_since = since_id is None
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            event = HarnessEvent.model_validate_json(line)
                        except Exception:
                            continue

                        if not found_since:
                            if event.id == since_id:
                                found_since = True
                            continue

                        if target_type_val is not None and event.event_type.value != target_type_val:
                            continue
                        if source is not None and event.source != source:
                            continue

                        dq.append(event)
            except OSError as e:
                logger.warning("Failed reading event log file", path=str(path), error=str(e))
                return

            yield from dq
            return

        found_since = since_id is None
        try:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = HarnessEvent.model_validate_json(line)
                    except Exception:
                        continue

                    if not found_since:
                        if event.id == since_id:
                            found_since = True
                        continue

                    if target_type_val is not None and event.event_type.value != target_type_val:
                        continue
                    if source is not None and event.source != source:
                        continue

                    yield event
        except OSError as e:
            logger.warning("Failed reading event log file", path=str(path), error=str(e))

    @classmethod
    def read_log_file(
        cls,
        path: Path | str,
        *,
        event_type: EventType | str | None = None,
        source: str | None = None,
        limit: int | None = None,
        since_id: str | None = None,
    ) -> list[HarnessEvent]:
        """Read and parse events from a persistent JSONL log file.

        Args:
            path: Path to the JSONL log file.
            event_type: Optional event type filter (enum or string value).
            source: Optional source plugin filter.
            limit: Maximum number of recent events to return.
            since_id: Event ID to start after.

        Returns:
            List of parsed and filtered HarnessEvent instances.
        """
        return list(
            cls.iter_log_file(
                path,
                event_type=event_type,
                source=source,
                limit=limit,
                since_id=since_id,
            )
        )

    async def replay_stream(
        self,
        *,
        from_timestamp: float | datetime | str | None = None,
        to_timestamp: float | datetime | str | None = None,
        event_types: list[EventType | str] | None = None,
        source: str | None = None,
    ) -> AsyncIterator[HarnessEvent]:
        """Asynchronously stream historical events matching time ranges and criteria in strict chronological order.

        Args:
            from_timestamp: Optional minimum timestamp inclusive.
            to_timestamp: Optional maximum timestamp inclusive.
            event_types: Optional list of event types to include.
            source: Optional source plugin filter.

        Yields:
            Matching HarnessEvent instances in chronological sequence.
        """
        def _to_epoch(val: float | int | datetime | str | None) -> float | None:
            if val is None:
                return None
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, datetime):
                return val.timestamp()
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val).timestamp()
                except Exception:
                    return None
            return None

        from_epoch = _to_epoch(from_timestamp)
        to_epoch = _to_epoch(to_timestamp)

        type_set: set[str] | None = None
        if event_types is not None:
            type_set = {
                t.value if isinstance(t, EventType) else str(t)
                for t in event_types
            }

        for event in list(self._log):
            event_epoch = (
                event.timestamp.timestamp()
                if isinstance(event.timestamp, datetime)
                else float(event.timestamp)
            )
            if from_epoch is not None and event_epoch < from_epoch:
                continue
            if to_epoch is not None and event_epoch > to_epoch:
                continue
            if type_set is not None and event.event_type.value not in type_set:
                continue
            if source is not None and event.source != source:
                continue
            yield event

    def clear(self) -> None:
        """Reset the in-memory event buffer for test harness isolation.

        Note:
            In accordance with Rule 4 (Append-Only Events), event records in persistent
            storage (JSONL) are strictly immutable and never truncated by this method.
        """
        self._log.clear()
        logger.info("Event log buffer reset")

    @property
    def handler_count(self) -> int:
        """Total number of registered handlers across all event types."""
        return sum(len(handlers) for handlers in self._handlers.values())

    async def _safe_call(
        self, handler: EventHandler, event: HarnessEvent
    ) -> None:
        """Call a handler with error isolation."""
        res = handler(event)
        if inspect.isawaitable(res):
            await res

    async def _persist_event(self, event: HarnessEvent) -> None:
        """Append event to the JSONL log file."""
        if self._log_file is None:
            return

        try:
            line = event.model_dump_json() + "\n"
            # Use synchronous write (events are small, atomicity matters more)
            with open(self._log_file, "a", encoding="utf-8") as f:  # noqa: ASYNC230
                f.write(line)
        except OSError as e:
            logger.warning("Failed to persist event", error=str(e))

    async def close(self) -> None:
        """Clean up resources."""
        if self._log_file_handle:
            self._log_file_handle.close()
            self._log_file_handle = None

    def __repr__(self) -> str:
        return (
            f"EventBus(events={len(self._log)}, "
            f"handlers={self.handler_count})"
        )


class EventProjection(ABC, Generic[T]):
    """Abstract base class for point-in-time state and metrics projections from events."""

    @abstractmethod
    def handle(self, event: HarnessEvent) -> None:
        """Process an incoming or replayed event to update internal projected state."""

    @abstractmethod
    def get_state(self) -> T:
        """Return the current computed projection snapshot."""

    def reset(self) -> None:
        """Reset projection state to its initial empty baseline."""


class MetricsProjection(EventProjection[dict[str, Any]]):
    """Computes runtime performance, latency, error rate, and token usage metrics."""

    def __init__(self) -> None:
        self.total_events: int = 0
        self.event_counts_by_type: dict[str, int] = defaultdict(int)
        self.tool_invocations: dict[str, int] = defaultdict(int)
        self.tool_errors: dict[str, int] = defaultdict(int)
        self.tool_results: dict[str, int] = defaultdict(int)
        self.total_tokens: int = 0
        self.llm_calls: int = 0

    def handle(self, event: HarnessEvent) -> None:
        self.total_events += 1
        etype = event.event_type.value if isinstance(event.event_type, EventType) else str(event.event_type)
        self.event_counts_by_type[etype] += 1

        payload = event.payload or {}
        if event.event_type == EventType.TOOL_INVOKED:
            tool_name = payload.get("tool", "unknown")
            self.tool_invocations[tool_name] += 1
        elif event.event_type == EventType.TOOL_RESULT:
            tool_name = payload.get("tool", "unknown")
            self.tool_results[tool_name] += 1
        elif event.event_type == EventType.TOOL_ERROR:
            tool_name = payload.get("tool", "unknown")
            self.tool_errors[tool_name] += 1
        elif event.event_type == EventType.LLM_RESPONSE:
            self.llm_calls += 1
            usage = payload.get("usage", {})
            if isinstance(usage, dict):
                self.total_tokens += usage.get("total_tokens", 0)

    def get_state(self) -> dict[str, Any]:
        return {
            "total_events": self.total_events,
            "event_counts_by_type": dict(self.event_counts_by_type),
            "tool_invocations": dict(self.tool_invocations),
            "tool_results": dict(self.tool_results),
            "tool_errors": dict(self.tool_errors),
            "total_tokens": self.total_tokens,
            "llm_calls": self.llm_calls,
        }

    def reset(self) -> None:
        self.total_events = 0
        self.event_counts_by_type.clear()
        self.tool_invocations.clear()
        self.tool_errors.clear()
        self.tool_results.clear()
        self.total_tokens = 0
        self.llm_calls = 0


class AuditProjection(EventProjection[list[dict[str, Any]]]):
    """Aggregates security, lifecycle mutations, and access audit records."""

    def __init__(self, max_records: int = 1000) -> None:
        self.max_records = max_records
        self._records: deque[dict[str, Any]] = deque(maxlen=max_records)

    def handle(self, event: HarnessEvent) -> None:
        etype = event.event_type.value if isinstance(event.event_type, EventType) else str(event.event_type)
        etype_upper = etype.upper()
        if (
            "ERROR" in etype_upper
            or "SECURITY" in etype_upper
            or "PLUGIN" in etype_upper
            or "SYSTEM" in etype_upper
            or etype in (EventType.TOOL_INVOKED.value, EventType.TOOL_ERROR.value)
        ):
            record = {
                "id": event.id,
                "timestamp": event.timestamp.isoformat() if isinstance(event.timestamp, datetime) else str(event.timestamp),
                "event_type": etype,
                "source": event.source,
                "payload": event.payload,
            }
            self._records.append(record)

    def get_state(self) -> list[dict[str, Any]]:
        return list(self._records)

    def reset(self) -> None:
        self._records.clear()


class EventProjectionEngine:
    """Authoritative projection engine coordinating live and point-in-time views."""

    def __init__(self, bus: EventBus | None = None) -> None:
        self._projections: dict[str, EventProjection[Any]] = {}
        self._bus = bus
        if bus is not None:
            self.attach(bus)

    def attach(self, bus: EventBus, replay_existing: bool = True) -> None:
        """Attach projection engine to an EventBus."""
        self._bus = bus
        bus.on("*", self._on_event)
        if replay_existing:
            for event in bus.log:
                self._dispatch(event)

    def register(self, name: str, projection: EventProjection[Any]) -> None:
        """Register a projection by name."""
        self._projections[name] = projection
        if self._bus is not None:
            for event in self._bus.log:
                projection.handle(event)

    def get(self, name: str) -> EventProjection[Any] | None:
        """Retrieve projection by name."""
        return self._projections.get(name)

    def get_state(self, name: str) -> Any:
        """Get state of a named projection."""
        proj = self.get(name)
        return proj.get_state() if proj is not None else None

    async def _on_event(self, event: HarnessEvent) -> None:
        self._dispatch(event)

    def _dispatch(self, event: HarnessEvent) -> None:
        for proj in self._projections.values():
            try:
                proj.handle(event)
            except Exception as e:
                logger.warning("Projection handling error", error=str(e))
