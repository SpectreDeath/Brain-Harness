"""Exercise 01.03: Immutable Event Bus (Problem)."""

from __future__ import annotations

from harness.events.bus import EventBus
from harness.events.types import HarnessEvent


async def run_event_pipeline() -> tuple[EventBus, list[HarnessEvent]]:
    bus = EventBus()
    captured_events: list[HarnessEvent] = []

    # TODO: Define an async listener that appends events to captured_events
    # TODO: Subscribe listener to bus using bus.on(EventType.PLUGIN_ENABLED, listener)
    # TODO: Emit a HarnessEvent of EventType.PLUGIN_ENABLED with source "test" and payload {"plugin": "custom"}

    return bus, captured_events
