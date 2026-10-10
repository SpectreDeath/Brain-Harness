"""Persistent JSONL event logging and lazy stream parsing per AGENTS.md Rule 4."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from ..types import EventType, HarnessEvent

logger = structlog.get_logger()


async def persist_event(log_file: Path | None, event: HarnessEvent) -> None:
    """Append event to the JSONL log file asynchronously/atomically."""
    if log_file is None:
        return

    try:
        line = event.model_dump_json() + "\n"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError as e:
        logger.warning("Failed to persist event", error=str(e))


def persist_event_sync(log_file: Path | None, event: HarnessEvent) -> None:
    """Append event to the JSONL log file synchronously."""
    if log_file is None:
        return

    try:
        line = event.model_dump_json() + "\n"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError as e:
        logger.warning("Failed to persist event", error=str(e))


def iter_log_file(
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
    from ..types import EventType as _EventType, HarnessEvent as _HarnessEvent

    p = Path(path)
    if not p.exists() or not p.is_file():
        return

    target_type_val: str | None = None
    if event_type is not None:
        target_type_val = (
            event_type.value if isinstance(event_type, _EventType) else str(event_type)
        )

    if limit is not None and limit > 0:
        dq: deque[_HarnessEvent] = deque(maxlen=limit)
        found_since = since_id is None
        try:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = _HarnessEvent.model_validate_json(line)
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
                    event = _HarnessEvent.model_validate_json(line)
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


def read_log_file(
    path: Path | str,
    *,
    event_type: EventType | str | None = None,
    source: str | None = None,
    limit: int | None = None,
    since_id: str | None = None,
) -> list[HarnessEvent]:
    """Read and parse events from a persistent JSONL log file into a list."""
    return list(
        iter_log_file(
            path,
            event_type=event_type,
            source=source,
            limit=limit,
            since_id=since_id,
        )
    )
