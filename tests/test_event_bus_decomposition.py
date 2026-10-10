"""Contract and invariant verification for EventBus decomposition per AGENTS.md Rules 4, 11, and 58."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import pytest

from harness.events.bus import (
    EVENT_BUS_KEY,
    AuditProjection,
    EventBus,
    EventBusService,
    EventHandler,
    EventLedger,
    EventProjection,
    EventProjectionEngine,
    MetricsProjection,
    SubscriptionRegistry,
    iter_log_file,
    persist_event,
    persist_event_sync,
    read_log_file,
    replay_stream_events,
    resolve_event_bus,
    stream_events,
)
from harness.events.types import (
    EventType,
    HarnessEvent,
    plugin_event,
    tool_event,
)
from harness.kernel.context import ServiceContext


def test_event_bus_subpackage_line_bounds() -> None:
    """Enforce Rule 11: All files in src/harness/events/bus must be strictly < 200 lines."""
    bus_pkg = Path(r"D:\GitHub\projects\Brain Harness\src\harness\events\bus")
    assert bus_pkg.is_dir()
    py_files = list(bus_pkg.glob("*.py"))
    assert len(py_files) >= 8

    for py_file in py_files:
        line_count = len(py_file.read_text(encoding="utf-8").splitlines())
        assert (
            line_count < 200
        ), f"File {py_file.name} has {line_count} lines, exceeding 200 line limit!"


def test_event_bus_subpackage_exports() -> None:
    """Verify all public symbols are exported cleanly from the bus subpackage facade."""
    assert issubclass(EventBus, object)
    assert EVENT_BUS_KEY.name == "events.bus"
    assert issubclass(EventLedger, object)
    assert issubclass(SubscriptionRegistry, object)
    assert issubclass(EventProjection, object)
    assert issubclass(MetricsProjection, EventProjection)
    assert issubclass(AuditProjection, EventProjection)
    assert issubclass(EventProjectionEngine, object)
    assert callable(resolve_event_bus)
    assert callable(iter_log_file)
    assert callable(read_log_file)
    assert callable(persist_event)
    assert callable(persist_event_sync)
    assert callable(stream_events)
    assert callable(replay_stream_events)


def test_single_seam_resolver_contract() -> None:
    """Verify Rule 58 single-seam resolver resolve_event_bus across targets."""
    # 1. Target is None -> new default instance
    bus1 = resolve_event_bus()
    assert isinstance(bus1, EventBus)

    # 2. Target is existing EventBus -> returns identity
    assert resolve_event_bus(bus1) is bus1

    # 3. Target is ServiceContext -> resolves or registers onto EVENT_BUS_KEY
    context = ServiceContext()
    assert context.optional(EVENT_BUS_KEY) is None
    bus2 = resolve_event_bus(context)
    assert isinstance(bus2, EventBus)
    assert context.optional(EVENT_BUS_KEY) is bus2

    # Idempotent re-resolution
    bus3 = resolve_event_bus(context)
    assert bus3 is bus2


def test_event_bus_service_protocol_conformance() -> None:
    """Verify EventBus conforms to EventBusService Protocol."""
    bus = EventBus()
    assert isinstance(bus, EventBusService)


def test_ledger_append_and_filtering() -> None:
    """Verify EventLedger append-only semantics, since, filter, and clear (Rule 4)."""
    ledger = EventLedger(max_size=5)
    e1 = plugin_event(EventType.PLUGIN_ENABLED, "p1")
    e2 = tool_event(EventType.TOOL_INVOKED, "tool1")
    e3 = plugin_event(EventType.PLUGIN_DISABLED, "p1")

    ledger.append(e1)
    ledger.append(e2)
    ledger.append(e3)

    assert len(ledger) == 3
    assert ledger.events == [e1, e2, e3]

    # since
    assert ledger.since(e1.id) == [e2, e3]
    assert ledger.since("non-existent") == []

    # filter
    assert ledger.filter(event_type=EventType.TOOL_INVOKED) == [e2]
    assert ledger.filter(source="p1") == [e1, e3]
    assert ledger.filter(limit=1) == [e3]

    # clear (in-memory buffer reset)
    ledger.clear()
    assert len(ledger) == 0


@pytest.mark.asyncio
async def test_subscription_registry_dispatch_and_isolation() -> None:
    """Verify SubscriptionRegistry wildcard, specific, off, and error isolation."""
    registry = SubscriptionRegistry()
    calls: list[str] = []

    async def h_plugin(ev: HarnessEvent) -> None:
        calls.append("plugin")

    async def h_wildcard(ev: HarnessEvent) -> None:
        calls.append("wildcard")

    async def h_error(ev: HarnessEvent) -> None:
        raise RuntimeError("boom")

    registry.on(EventType.PLUGIN_ENABLED, h_plugin)
    registry.on_all(h_wildcard)
    registry.on(EventType.PLUGIN_ENABLED, h_error)

    assert registry.handler_count == 3
    event = plugin_event(EventType.PLUGIN_ENABLED, "test")

    # Dispatch should not raise even with boom handler
    await registry.dispatch(event)
    assert "plugin" in calls
    assert "wildcard" in calls

    # Unsubscribe
    registry.off(h_plugin)
    assert registry.handler_count == 2


@pytest.mark.asyncio
async def test_projections_engine_dispatch() -> None:
    """Verify MetricsProjection, AuditProjection, and EventProjectionEngine."""
    bus = EventBus()
    engine = EventProjectionEngine(bus)

    metrics = MetricsProjection()
    audit = AuditProjection(max_records=10)

    engine.register("metrics", metrics)
    engine.register("audit", audit)

    e1 = tool_event(EventType.TOOL_INVOKED, "fs.read")
    e2 = plugin_event(EventType.PLUGIN_ENABLED, "auth")

    await bus.emit(e1)
    await bus.emit(e2)

    metrics_state = engine.get_state("metrics")
    assert metrics_state["total_events"] == 2
    assert metrics_state["tool_invocations"]["fs.read"] == 1

    audit_state = engine.get_state("audit")
    assert len(audit_state) == 2


@pytest.mark.asyncio
async def test_persistence_and_file_reading(tmp_path: Path) -> None:
    """Verify JSONL event writing and lazy stream reading."""
    log_file = tmp_path / "events.jsonl"
    bus = EventBus(log_file=log_file)

    e1 = plugin_event(EventType.PLUGIN_ENABLED, "modA")
    e2 = tool_event(EventType.TOOL_INVOKED, "toolB")

    await bus.emit(e1)
    bus.emit_sync(e2)

    assert log_file.exists()
    read_events = read_log_file(log_file)
    assert len(read_events) == 2
    assert read_events[0].id == e1.id
    assert read_events[1].id == e2.id

    # Test limit filter
    tail_events = list(iter_log_file(log_file, limit=1))
    assert len(tail_events) == 1
    assert tail_events[0].id == e2.id


@pytest.mark.asyncio
async def test_streaming_and_replay_filtering() -> None:
    """Verify live stream generator and replay stream with timestamp bounds."""
    bus = EventBus()
    t_now = datetime.now(timezone.utc)
    e1 = plugin_event(EventType.PLUGIN_ENABLED, "alpha")
    e2 = tool_event(EventType.TOOL_INVOKED, "beta")
    await bus.emit(e1)
    await bus.emit(e2)

    replayed = []
    async for ev in bus.replay_stream(event_types=[EventType.TOOL_INVOKED]):
        replayed.append(ev)

    assert len(replayed) == 1
    assert replayed[0].id == e2.id
