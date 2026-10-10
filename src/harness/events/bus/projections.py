"""Point-in-time state and metrics event projections."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import structlog

from ..types import EventType, HarnessEvent

if TYPE_CHECKING:
    from .core import EventBus

T = TypeVar("T")
logger = structlog.get_logger()


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
        etype = (
            event.event_type.value
            if isinstance(event.event_type, EventType)
            else str(event.event_type)
        )
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
        etype = (
            event.event_type.value
            if isinstance(event.event_type, EventType)
            else str(event.event_type)
        )
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
                "timestamp": (
                    event.timestamp.isoformat()
                    if isinstance(event.timestamp, datetime)
                    else str(event.timestamp)
                ),
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
