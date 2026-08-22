"""Tests for Architecture Deepening Cycle 7.

Validates:
1. EventBus.fire() context-aware emission and sync handler execution.
2. Lifecycle and context _emit_event delegation to fire().
3. Unified load-validate traversal in PluginLifecycle.enable_all().
4. Single-authority WebSocket streaming and channel filtering via UIProjectionEngine.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock

from harness.events.bus import EventBus
from harness.events.types import EventType, HarnessEvent
from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.lifecycle import PluginLifecycle, PluginState
from harness.kernel.runtime import HarnessRuntime
from harness.plugins.base import HarnessPlugin
from harness.services.tools import ToolRegistryPlugin
from harness.ui.server import create_app


class MockDiscoveryPlugin(HarnessPlugin):
    """Test plugin that provides a dummy service."""
    name = "mock.discovery"
    version = "1.0.0"
    provides = [ServiceKey("test.dummy")]

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(ServiceKey("test.dummy"), "dummy_value", provider=self.name)

    async def on_enable(self) -> None:
        pass

    async def on_disable(self) -> None:
        pass

    async def on_unload(self) -> None:
        pass


@pytest.mark.asyncio
async def test_event_bus_fire_sync_and_async() -> None:
    """Verify EventBus.fire() records events and dispatches to registered handlers."""
    bus = EventBus()
    received = []

    async def test_handler(event: HarnessEvent) -> None:
        received.append(event)

    bus.on(EventType.PLUGIN_DISCOVERED, test_handler)

    # Fire an event using .fire()
    event = HarnessEvent(
        event_type=EventType.PLUGIN_DISCOVERED,
        source="test",
        payload={"plugin": "test_plugin"},
    )
    bus.fire(event)

    # Event should be immediately in the append-only log
    assert len(bus.log) == 1
    assert bus.log[0].payload["plugin"] == "test_plugin"

    # Allow event loop to tick for async handlers
    await asyncio.sleep(0.01)
    assert len(received) == 1
    assert received[0].payload["plugin"] == "test_plugin"


@pytest.mark.asyncio
async def test_lifecycle_and_context_delegation_to_fire() -> None:
    """Verify lifecycle transitions and service registrations fire events through bus."""
    ctx = ServiceContext()
    bus = EventBus()
    ctx.attach_event_bus(bus)
    lifecycle = PluginLifecycle(ctx, event_bus=bus)

    plugin = MockDiscoveryPlugin()
    lifecycle.discover(plugin)

    # Verify discovery event fired into bus
    events = bus.log
    assert any(e.event_type == EventType.PLUGIN_DISCOVERED for e in events)

    # Single call to enable_all should advance DISCOVERED -> LOADED -> VALIDATED -> ENABLED
    results = await lifecycle.enable_all()
    assert results[plugin.name] is True
    assert lifecycle.get_state(plugin.name) == PluginState.ENABLED
    assert ctx.has(ServiceKey("test.dummy"))

    # Verify service provided event
    events = bus.log
    assert any(e.event_type == EventType.SERVICE_PROVIDED for e in events)


@pytest.mark.asyncio
async def test_runtime_unified_enable_all() -> None:
    """Verify HarnessRuntime.enable_all_plugins() delegates cleanly to lifecycle."""
    async with HarnessRuntime.create(db_path=":memory:", builtins=[ToolRegistryPlugin()]) as rt:
        assert rt.lifecycle.get_state("tools.registry") == PluginState.ENABLED
        # Disable all
        await rt.disable_all_plugins(keep_core=False)
        assert rt.lifecycle.get_state("tools.registry") == PluginState.DISABLED

        # Re-enable all without redundant pre-flight loops
        results = await rt.enable_all_plugins()
        assert results["tools.registry"] is True
        assert rt.lifecycle.get_state("tools.registry") == PluginState.ENABLED


@pytest.mark.asyncio
async def test_ui_server_single_websocket_authority() -> None:
    """Verify UI server routes WebSocket and projections through UIProjectionEngine without duplication."""
    ctx = ServiceContext()
    lifecycle = PluginLifecycle(ctx)
    bus = EventBus()

    app = create_app(ctx, lifecycle, event_bus=bus)
    engine = app.state.projection_engine
    assert engine is not None

    mock_ws = AsyncMock()
    sub = await engine.connect_client(mock_ws, initial_channels={"system", "events"})
    assert sub.is_subscribed("system")

    # Fire event via bus.fire
    bus.fire(HarnessEvent(event_type=EventType.HARNESS_STARTED, source="core", payload={}))

    # Allow async dispatcher to process
    await asyncio.sleep(0.01)

    # Verify feed in engine recorded single entry
    feed = engine.get_activity_feed(channel="system")
    assert len(feed) == 1
    assert feed[0]["event_type"] == EventType.HARNESS_STARTED.value
