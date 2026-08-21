"""Tests for UIProjectionEngine, Ecosystem Bridge capabilities, and ConfigurationReconciler drift detection."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from harness.bridges.base import BridgeCapability, EcosystemBridgeCatalog, EcosystemBridgePlugin
from harness.bridges.em_cubed import EmCubedPlugin
from harness.bridges.flywheel import FlywheelBridgePlugin
from harness.bridges.memtext import MemtextServicePlugin
from harness.events.bus import EventBus
from harness.events.types import EventType, HarnessEvent
from harness.kernel.context import ServiceContext
from harness.kernel.reconciler import ConfigurationReconciler, HarnessConfigTree, PluginConfigEntry
from harness.kernel.runtime import HarnessRuntime
from harness.ui.projection import UIProjectionEngine


@pytest.mark.asyncio
async def test_ui_projection_engine_channels_and_feed() -> None:
    """Verify UIProjectionEngine filters event channels and manages client subscriptions."""
    bus = EventBus()
    engine = UIProjectionEngine(event_bus=bus)

    mock_ws = AsyncMock()
    sub = await engine.connect_client(mock_ws, initial_channels={"swarm", "metrics"})
    assert sub.is_subscribed("swarm")
    assert not sub.is_subscribed("agent")

    # Send client message to change subscriptions
    await engine.handle_client_message(
        mock_ws, '{"type": "subscribe", "channels": ["agent", "events"]}'
    )
    assert sub.is_subscribed("agent")
    assert not sub.is_subscribed("swarm")

    # Emit event through bus
    event = HarnessEvent(
        event_type=EventType.AGENT_TASK_STARTED,
        source="test",
        payload={"task": "Deepen codebase"},
    )
    await bus.emit(event)

    feed = engine.get_activity_feed(channel="agent")
    assert len(feed) == 1
    assert feed[0]["event_type"] == EventType.AGENT_TASK_STARTED.value

    status = engine.get_projection_status()
    assert status["active_clients"] == 1
    assert status["feed_size"] == 1

    engine.disconnect_client(mock_ws)
    assert len(engine._subscriptions) == 0


@pytest.mark.asyncio
async def test_ecosystem_bridge_capabilities_and_health_check() -> None:
    """Verify ecosystem bridges expose capabilities and capability matrices."""
    # List by capability
    vector_bridges = EcosystemBridgeCatalog.find_bridges_by_capability(BridgeCapability.VECTOR_INDEX)
    assert EmCubedPlugin in vector_bridges

    memory_bridges = EcosystemBridgeCatalog.find_bridges_by_capability(BridgeCapability.MEMORY_GRAPH)
    assert MemtextServicePlugin in memory_bridges

    prompt_bridges = EcosystemBridgeCatalog.find_bridges_by_capability(BridgeCapability.PROMPT_OPTIMIZATION)
    assert FlywheelBridgePlugin in prompt_bridges

    matrix = EcosystemBridgeCatalog.get_capability_matrix()
    assert "em-cubed" in matrix
    assert BridgeCapability.CODE_EXECUTION.value in matrix["em-cubed"]
    assert BridgeCapability.MEMORY_GRAPH.value in matrix["Memtext"]

    # Health check
    em_plugin = EmCubedPlugin()
    health = await em_plugin.health_check()
    assert health["project_name"] == "em-cubed"
    assert "capabilities" in health
    assert health["status"] in ("healthy", "fallback")


@pytest.mark.asyncio
async def test_reconciler_drift_detection() -> None:
    """Verify ConfigurationReconciler accurately detects configuration drift without mutating state."""
    runtime = HarnessRuntime.create()
    reconciler = ConfigurationReconciler(runtime)

    # Initial drift comparison
    target_config = HarnessConfigTree(
        plugins=[
            PluginConfigEntry(id="p1", name="tools.registry", disabled=False),
            PluginConfigEntry(id="p2", name="custom.new_plugin", source="https://github.com/test/repo"),
        ]
    )

    drift = reconciler.detect_drift(target_config)
    assert drift.has_drift is True
    assert "custom.new_plugin" in drift.to_add
    assert "tools.registry" in drift.to_enable

    drift_dict = drift.to_dict()
    assert drift_dict["has_drift"] is True
    assert "custom.new_plugin" in drift_dict["to_add"]
    assert "tools.registry" in drift_dict["to_enable"]

    # Reconcile / enable tools.registry, then verify unchanged
    await runtime.lifecycle.load("tools.registry")
    await runtime.lifecycle.validate("tools.registry")
    await runtime.lifecycle.enable("tools.registry")

    # Set last config committed
    reconciler._last_config = {"p1": PluginConfigEntry(id="p1", name="tools.registry", disabled=False)}
    drift2 = reconciler.detect_drift([PluginConfigEntry(id="p1", name="tools.registry", disabled=False)])
    assert "tools.registry" in drift2.unchanged
