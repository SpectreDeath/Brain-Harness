"""Exercise 01.03: Immutable Event Bus (Solution)."""

from __future__ import annotations

from harness.events.bus import EventBus
from harness.events.types import EventType, HarnessEvent


async def run_event_pipeline() -> tuple[EventBus, list[HarnessEvent]]:
    bus = EventBus()
    captured_events: list[HarnessEvent] = []

    async def listener(event: HarnessEvent) -> None:
        captured_events.append(event)

    bus.on(EventType.PLUGIN_ENABLED, listener)

    await bus.emit(HarnessEvent(
        event_type=EventType.PLUGIN_ENABLED,
        source="test",
        payload={"plugin": "custom"},
    ))

    return bus, captured_events
