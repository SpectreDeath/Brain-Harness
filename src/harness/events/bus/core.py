"""Core EventBus implementation coordinating ledger, subscriptions, and persistence."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from .ledger import EventLedger
from .models import EventHandler
from .persistence import iter_log_file, persist_event, persist_event_sync, read_log_file
from .streaming import replay_stream_events, stream_events
from .subscriptions import SubscriptionRegistry

if TYPE_CHECKING:
    from datetime import datetime
    from ..types import EventType, HarnessEvent

logger = structlog.get_logger()


class EventBus:
    """Async pub/sub event bus with append-only event log (AGENTS.md Rule 4)."""

    def __init__(
        self,
        max_log_size: int = 10_000,
        log_file: Path | None = None,
    ) -> None:
        self._ledger = EventLedger(max_size=max_log_size)
        self._registry = SubscriptionRegistry()
        self._log_file = log_file
        self._log_file_handle: Any = None

        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)

    @property
    def _log(self) -> Any:
        """Internal ledger deque for backward compatibility."""
        return self._ledger._log

    @property
    def _handlers(self) -> dict[str, list[EventHandler]]:
        """Internal handler registry map for backward compatibility."""
        return self._registry.handlers

    async def emit(self, event: HarnessEvent) -> None:
        """Emit an event asynchronously to all subscribed handlers."""
        self._ledger.append(event)
        if self._log_file:
            await persist_event(self._log_file, event)
        await self._registry.dispatch(event)

    def emit_sync(self, event: HarnessEvent) -> None:
        """Emit an event synchronously and schedule async handlers on active loop."""
        self._ledger.append(event)
        if self._log_file:
            persist_event_sync(self._log_file, event)

        handlers = self._registry.get_handlers(event.event_type.value)
        if handlers:
            try:
                loop = asyncio.get_running_loop()
                for h in handlers:
                    loop.create_task(self._registry.safe_call(h, event))
            except RuntimeError:
                pass

    def fire(self, event: HarnessEvent) -> None:
        """Canonical context-aware emission seam: appends immediately and persists."""
        self.emit_sync(event)

    def on(self, event_type: EventType | str, handler: EventHandler) -> None:
        """Subscribe a handler to an event type."""
        self._registry.on(event_type, handler)

    subscribe = on

    def off(self, handler: EventHandler) -> None:
        """Unsubscribe a handler from all event types."""
        self._registry.off(handler)

    def on_all(self, handler: EventHandler) -> None:
        """Subscribe a handler to ALL event types."""
        self._registry.on_all(handler)

    @property
    def log(self) -> list[HarnessEvent]:
        """Return a copy of the event log (most recent events)."""
        return self._ledger.events

    def log_since(self, after_id: str | None = None) -> list[HarnessEvent]:
        """Return events emitted after a given event ID."""
        return self._ledger.since(after_id)

    def filter_log(
        self,
        event_type: EventType | None = None,
        source: str | None = None,
        limit: int | None = None,
    ) -> list[HarnessEvent]:
        """Filter the event log by type and/or source."""
        return self._ledger.filter(event_type=event_type, source=source, limit=limit)

    async def stream(
        self,
        event_type: EventType | str | None = None,
        source: str | None = None,
        *,
        since_id: str | None = None,
        replay_history: bool = True,
        queue_size: int = 1000,
    ) -> AsyncIterator[HarnessEvent]:
        """Stream events asynchronously as they are emitted to the bus."""
        async for event in stream_events(
            self,
            event_type=event_type,
            source=source,
            since_id=since_id,
            replay_history=replay_history,
            queue_size=queue_size,
        ):
            yield event

    iter_log_file = staticmethod(iter_log_file)
    read_log_file = staticmethod(read_log_file)

    async def replay_stream(
        self,
        *,
        from_timestamp: float | datetime | str | None = None,
        to_timestamp: float | datetime | str | None = None,
        event_types: list[EventType | str] | None = None,
        source: str | None = None,
    ) -> AsyncIterator[HarnessEvent]:
        """Asynchronously stream historical events matching time ranges and criteria."""
        async for event in replay_stream_events(
            self.log,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            event_types=event_types,
            source=source,
        ):
            yield event

    def clear(self) -> None:
        """Reset the in-memory event buffer for test harness isolation."""
        self._ledger.clear()

    @property
    def handler_count(self) -> int:
        """Total number of registered handlers across all event types."""
        return self._registry.handler_count

    async def _safe_call(self, handler: EventHandler, event: HarnessEvent) -> None:
        """Call a handler with error isolation."""
        await self._registry.safe_call(handler, event)

    async def _persist_event(self, event: HarnessEvent) -> None:
        """Append event to the JSONL log file."""
        await persist_event(self._log_file, event)

    async def close(self) -> None:
        """Clean up resources."""
        if self._log_file_handle:
            self._log_file_handle.close()
            self._log_file_handle = None

    def __repr__(self) -> str:
        return f"EventBus(events={len(self._ledger)}, handlers={self.handler_count})"
