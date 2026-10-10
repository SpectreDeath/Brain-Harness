"""Append-only in-memory event ledger per AGENTS.md Rule 4."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from ..types import EventType, HarnessEvent

logger = structlog.get_logger()


class EventLedger:
    """Encapsulates the in-memory append-only ring buffer for events.

    In accordance with AGENTS.md Rule 4, events in the log are immutable
    and append-only.
    """

    __slots__ = ("_log", "_max_size")

    def __init__(self, max_size: int = 10_000) -> None:
        self._max_size = max_size
        self._log: deque[HarnessEvent] = deque(maxlen=max_size)

    def append(self, event: HarnessEvent) -> None:
        """Append an event to the ledger."""
        self._log.append(event)

    @property
    def events(self) -> list[HarnessEvent]:
        """Return a snapshot copy of the in-memory ledger."""
        return list(self._log)

    def since(self, after_id: str | None = None) -> list[HarnessEvent]:
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

    def filter(
        self,
        event_type: EventType | None = None,
        source: str | None = None,
        limit: int | None = None,
    ) -> list[HarnessEvent]:
        """Filter the ledger by event type and/or source.

        Args:
            event_type: Filter by event type.
            source: Filter by source identifier.
            limit: Maximum number of recent events to return.
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

    def clear(self) -> None:
        """Reset the in-memory event buffer for test harness isolation.

        Note:
            In accordance with Rule 4 (Append-Only Events), event records in persistent
            storage (JSONL) are strictly immutable and never truncated by this method.
        """
        self._log.clear()
        logger.info("Event log buffer reset")

    def __len__(self) -> int:
        return len(self._log)

    def __iter__(self) -> Iterator[HarnessEvent]:
        return iter(list(self._log))
