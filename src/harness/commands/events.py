"""Event commands — pure async and sync functions for reading and querying event streams."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from harness.events.types import HarnessEvent

logger = structlog.get_logger()


@dataclass
class EventQueryResult:
    """Outcome of querying the Harness event log."""

    events: list[HarnessEvent] = field(default_factory=list)
    total_count: int = 0
    filtered_count: int = 0
    log_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_count": self.total_count,
            "filtered_count": self.filtered_count,
            "log_path": str(self.log_path) if self.log_path else None,
            "events": [e.to_dict() for e in self.events],
        }


def get_events_cmd(
    event_type: str | None = None,
    limit: int = 50,
    log_path: Path | str | None = None,
) -> EventQueryResult:
    """Read and filter events from the append-only event log file.

    Args:
        event_type: Optional event type string to filter by.
        limit: Maximum number of events to return.
        log_path: Path to events.jsonl file (defaults to .harness/events.jsonl).

    Returns:
        EventQueryResult containing list of matched HarnessEvent records.
    """
    from harness.events.bus import EventBus

    p = Path(log_path).resolve() if log_path else Path(".harness") / "events.jsonl"
    if not p.exists():
        logger.info("No event log file found", path=str(p))
        return EventQueryResult(events=[], total_count=0, filtered_count=0, log_path=p)

    events = EventBus.read_log_file(p, event_type=event_type, limit=limit)
    logger.info("Queried event log", count=len(events), event_type=event_type)

    return EventQueryResult(
        events=events,
        total_count=len(events),
        filtered_count=len(events),
        log_path=p,
    )


__all__ = [
    "EventQueryResult",
    "get_events_cmd",
]
