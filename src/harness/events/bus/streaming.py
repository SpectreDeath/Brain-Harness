"""Asynchronous live event streaming and chronological historical replay."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from ..types import EventType, HarnessEvent
    from .core import EventBus

logger = structlog.get_logger()


def to_epoch(val: float | int | datetime | str | None) -> float | None:
    """Normalize numeric, datetime, or ISO string timestamps to UTC epoch seconds."""
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


async def stream_events(
    bus: EventBus,
    event_type: EventType | str | None = None,
    source: str | None = None,
    *,
    since_id: str | None = None,
    replay_history: bool = True,
    queue_size: int = 1000,
) -> AsyncIterator[HarnessEvent]:
    """Stream events asynchronously as they are emitted to the bus."""
    from ..types import EventType as _EventType, HarnessEvent as _HarnessEvent

    queue: asyncio.Queue[_HarnessEvent] = asyncio.Queue(maxsize=queue_size)
    target_type_val: str | None = None
    if event_type is not None:
        target_type_val = (
            event_type.value if isinstance(event_type, _EventType) else str(event_type)
        )

    async def _stream_handler(event: _HarnessEvent) -> None:
        if target_type_val is not None and event.event_type.value != target_type_val:
            return
        if source is not None and event.source != source:
            return
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("Event stream queue full, dropping event", event_id=event.id)

    sub_key = target_type_val if target_type_val is not None else "*"
    bus.on(sub_key, _stream_handler)

    try:
        if replay_history:
            history = bus.log_since(since_id) if since_id else bus.log
            for h_event in history:
                if target_type_val is not None and h_event.event_type.value != target_type_val:
                    continue
                if source is not None and h_event.source != source:
                    continue
                yield h_event

        while True:
            live_event = await queue.get()
            yield live_event
    finally:
        bus.off(_stream_handler)


async def replay_stream_events(
    events: list[HarnessEvent],
    *,
    from_timestamp: float | datetime | str | None = None,
    to_timestamp: float | datetime | str | None = None,
    event_types: list[EventType | str] | None = None,
    source: str | None = None,
) -> AsyncIterator[HarnessEvent]:
    """Asynchronously stream events matching time ranges and criteria in strict chronological order."""
    from ..types import EventType as _EventType

    from_epoch = to_epoch(from_timestamp)
    to_epoch_val = to_epoch(to_timestamp)

    type_set: set[str] | None = None
    if event_types is not None:
        type_set = {
            t.value if isinstance(t, _EventType) else str(t)
            for t in event_types
        }

    for event in events:
        event_epoch = (
            event.timestamp.timestamp()
            if isinstance(event.timestamp, datetime)
            else float(event.timestamp)
        )
        if from_epoch is not None and event_epoch < from_epoch:
            continue
        if to_epoch_val is not None and event_epoch > to_epoch_val:
            continue
        if type_set is not None and event.event_type.value not in type_set:
            continue
        if source is not None and event.source != source:
            continue
        yield event
