"""Tests for the EventBus and event types."""

from pathlib import Path

import pytest

from harness.events.bus import EventBus
from harness.events.types import (
    EventType,
    HarnessEvent,
    ingestion_event,
    plugin_event,
    service_event,
    tool_event,
)


@pytest.mark.unit
class TestHarnessEvent:
    def test_create_event(self) -> None:
        event = HarnessEvent(event_type=EventType.HARNESS_STARTED)
        assert event.event_type == EventType.HARNESS_STARTED
        assert event.source == "harness"
        assert event.id  # Should have auto-generated ID
        assert event.timestamp  # Should have auto-generated timestamp

    def test_event_is_frozen(self) -> None:
        from pydantic import ValidationError

        event = HarnessEvent(event_type=EventType.HARNESS_STARTED)
        with pytest.raises(ValidationError):
            event.source = "changed"  # type: ignore

    def test_plugin_event_factory(self) -> None:
        event = plugin_event(EventType.PLUGIN_ENABLED, "my-plugin", extra="data")
        assert event.event_type == EventType.PLUGIN_ENABLED
        assert event.source == "my-plugin"
        assert event.payload["plugin"] == "my-plugin"
        assert event.payload["extra"] == "data"

    def test_service_event_factory(self) -> None:
        event = service_event(
            EventType.SERVICE_PROVIDED, "llm.provider", provider="llm-plugin"
        )
        assert event.payload["service"] == "llm.provider"
        assert event.payload["provider"] == "llm-plugin"

    def test_tool_event_factory(self) -> None:
        event = tool_event(EventType.TOOL_INVOKED, "git.clone")
        assert event.payload["tool"] == "git.clone"

    def test_ingestion_event_factory(self) -> None:
        event = ingestion_event(
            EventType.REPO_FETCH_STARTED,
            "https://github.com/owner/repo",
        )
        assert event.payload["url"] == "https://github.com/owner/repo"


@pytest.mark.unit
@pytest.mark.asyncio
class TestEventBus:
    async def test_emit_and_log(self) -> None:
        bus = EventBus()
        event = HarnessEvent(event_type=EventType.HARNESS_STARTED)
        await bus.emit(event)
        assert len(bus.log) == 1
        assert bus.log[0] is event

    async def test_handler_called(self) -> None:
        bus = EventBus()
        received: list[HarnessEvent] = []

        async def handler(event: HarnessEvent) -> None:
            received.append(event)

        bus.on(EventType.PLUGIN_ENABLED, handler)
        event = plugin_event(EventType.PLUGIN_ENABLED, "test")
        await bus.emit(event)

        assert len(received) == 1
        assert received[0] is event

    async def test_handler_not_called_for_wrong_type(self) -> None:
        bus = EventBus()
        received: list[HarnessEvent] = []

        async def handler(event: HarnessEvent) -> None:
            received.append(event)

        bus.on(EventType.PLUGIN_ENABLED, handler)
        event = HarnessEvent(event_type=EventType.HARNESS_STARTED)
        await bus.emit(event)

        assert len(received) == 0

    async def test_wildcard_handler(self) -> None:
        bus = EventBus()
        received: list[HarnessEvent] = []

        async def handler(event: HarnessEvent) -> None:
            received.append(event)

        bus.on_all(handler)

        await bus.emit(HarnessEvent(event_type=EventType.HARNESS_STARTED))
        await bus.emit(plugin_event(EventType.PLUGIN_ENABLED, "test"))

        assert len(received) == 2

    async def test_off_removes_handler(self) -> None:
        bus = EventBus()
        received: list[HarnessEvent] = []

        async def handler(event: HarnessEvent) -> None:
            received.append(event)

        bus.on(EventType.HARNESS_STARTED, handler)
        bus.off(handler)

        await bus.emit(HarnessEvent(event_type=EventType.HARNESS_STARTED))
        assert len(received) == 0

    async def test_handler_error_isolation(self) -> None:
        bus = EventBus()
        good_received: list[HarnessEvent] = []

        async def bad_handler(event: HarnessEvent) -> None:
            raise RuntimeError("oops")

        async def good_handler(event: HarnessEvent) -> None:
            good_received.append(event)

        bus.on(EventType.HARNESS_STARTED, bad_handler)
        bus.on(EventType.HARNESS_STARTED, good_handler)

        event = HarnessEvent(event_type=EventType.HARNESS_STARTED)
        await bus.emit(event)

        # Good handler should still receive the event
        assert len(good_received) == 1

    async def test_log_bounded(self) -> None:
        bus = EventBus(max_log_size=5)
        for i in range(10):
            await bus.emit(HarnessEvent(event_type=EventType.CUSTOM))

        assert len(bus.log) == 5

    async def test_filter_log(self) -> None:
        bus = EventBus()
        await bus.emit(HarnessEvent(event_type=EventType.HARNESS_STARTED))
        await bus.emit(plugin_event(EventType.PLUGIN_ENABLED, "a"))
        await bus.emit(plugin_event(EventType.PLUGIN_ENABLED, "b"))

        filtered = bus.filter_log(event_type=EventType.PLUGIN_ENABLED)
        assert len(filtered) == 2

    async def test_filter_by_source(self) -> None:
        bus = EventBus()
        await bus.emit(plugin_event(EventType.PLUGIN_ENABLED, "a"))
        await bus.emit(plugin_event(EventType.PLUGIN_ENABLED, "b"))

        filtered = bus.filter_log(source="a")
        assert len(filtered) == 1
        assert filtered[0].source == "a"

    async def test_clear(self) -> None:
        bus = EventBus()
        await bus.emit(HarnessEvent(event_type=EventType.HARNESS_STARTED))
        bus.clear()
        assert len(bus.log) == 0

    async def test_handler_count(self) -> None:
        bus = EventBus()

        async def h1(e: HarnessEvent) -> None:
            pass

        async def h2(e: HarnessEvent) -> None:
            pass

        bus.on(EventType.HARNESS_STARTED, h1)
        bus.on(EventType.PLUGIN_ENABLED, h2)
        assert bus.handler_count == 2

    async def test_persist_to_file(self, tmp_path: Path) -> None:
        log_file = tmp_path / "events.jsonl"
        bus = EventBus(log_file=log_file)
        await bus.emit(HarnessEvent(event_type=EventType.HARNESS_STARTED))
        await bus.emit(plugin_event(EventType.PLUGIN_ENABLED, "test"))

        assert log_file.exists()
        lines = log_file.read_text().strip().split("\n")
        assert len(lines) == 2

    async def test_read_log_file(self, tmp_path: Path) -> None:
        log_file = tmp_path / "events_read.jsonl"
        bus = EventBus(log_file=log_file)

        e1 = HarnessEvent(event_type=EventType.HARNESS_STARTED, source="core")
        e2 = plugin_event(EventType.PLUGIN_ENABLED, "plug_a", source="plug_a")
        e3 = plugin_event(EventType.PLUGIN_DISABLED, "plug_a", source="plug_a")
        e4 = plugin_event(EventType.PLUGIN_ENABLED, "plug_b", source="plug_b")

        await bus.emit(e1)
        await bus.emit(e2)
        await bus.emit(e3)
        await bus.emit(e4)

        # Read all
        all_events = EventBus.read_log_file(log_file)
        assert len(all_events) == 4

        # Read nonexistent
        assert EventBus.read_log_file(tmp_path / "does_not_exist.jsonl") == []

        # Filter by event_type
        enabled_evts = EventBus.read_log_file(log_file, event_type=EventType.PLUGIN_ENABLED)
        assert len(enabled_evts) == 2
        assert all(e.event_type == EventType.PLUGIN_ENABLED for e in enabled_evts)

        # Filter by source and limit
        plug_a_evts = EventBus.read_log_file(log_file, source="plug_a", limit=1)
        assert len(plug_a_evts) == 1
        assert plug_a_evts[0].event_type == EventType.PLUGIN_DISABLED

        # Test since_id
        after_e2 = EventBus.read_log_file(log_file, since_id=e2.id)
        assert len(after_e2) == 2
        assert [e.id for e in after_e2] == [e3.id, e4.id]

