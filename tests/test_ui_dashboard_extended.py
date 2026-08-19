"""Tests for extended UI endpoints, timeline event sourcing, and sandboxes monitor."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from harness.events.bus import EventBus
from harness.events.types import EventType, HarnessEvent
from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle
from harness.services.tools import ToolRegistryPlugin
from harness.ui.server import create_app


@pytest.mark.unit
@pytest.mark.asyncio
class TestUIDashboardExtended:
    async def test_timeline_metrics_and_sandboxes_endpoints(self) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)
        bus = EventBus()

        tools_plugin = ToolRegistryPlugin()
        lifecycle.discover(tools_plugin)
        await lifecycle.load(tools_plugin.name)
        await lifecycle.validate(tools_plugin.name)
        await lifecycle.enable(tools_plugin.name)

        # Emit some events
        await bus.emit(HarnessEvent(event_type=EventType.HARNESS_STARTED, source="kernel"))
        await bus.emit(HarnessEvent(event_type=EventType.TOOL_REGISTERED, source="tools.registry", payload={"tool": "echo"}))
        await bus.emit(HarnessEvent(event_type=EventType.PLUGIN_ENABLED, source="tools.registry", payload={"plugin": "tools.registry"}))

        app = create_app(ctx, lifecycle, bus)
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Timeline API
            timeline_res = await client.get("/api/timeline")
            assert timeline_res.status_code == 200
            t_data = timeline_res.json()
            assert t_data["total"] >= 3
            assert len(t_data["events"]) >= 3
            assert "summary" in t_data
            assert "counts_by_type" in t_data["summary"]

            # Filter timeline by event_type
            filtered_res = await client.get(f"/api/timeline?event_type={EventType.TOOL_REGISTERED.value}")
            assert filtered_res.status_code == 200
            f_data = filtered_res.json()
            assert f_data["total"] == 1
            assert f_data["events"][0]["event_type"] == EventType.TOOL_REGISTERED.value

            # 2. Metrics API
            metrics_res = await client.get("/api/metrics")
            assert metrics_res.status_code == 200
            m_data = metrics_res.json()
            assert m_data["total_events"] >= 3
            assert "event_counts_by_type" in m_data

            # 3. Sandboxes API
            sandboxes_res = await client.get("/api/sandboxes")
            assert sandboxes_res.status_code == 200
            s_data = sandboxes_res.json()
            assert s_data["total"] == 1
            assert s_data["sandboxes"][0]["plugin"] == "tools.registry"

            # 4. Swarm Status API
            swarm_res = await client.get("/api/swarm/status")
            assert swarm_res.status_code == 200
            assert swarm_res.json()["status"] == "ready"
