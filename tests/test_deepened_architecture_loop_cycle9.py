"""Comprehensive test suite for Architecture Deepening Loop — Cycle 9.

Verifies:
1. SwarmCoordinator run persistence, session tree storage, and async lookup across instances.
2. SwarmCoordinator run_swarm convenience workflow.
3. UI REST Server swarm endpoints (/api/swarm/runs, /api/swarm/runs/{run_id}, /api/swarm/runs/{run_id}/tree, /api/swarm/run).
4. MCPClientPlugin full-duplex mirroring of resources and prompts into MCPRegistry.
5. PluginCatalog event-driven invalidation and EventBus integration.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
import pytest
from httpx import ASGITransport, AsyncClient

from harness.agent.session import (
    AGENT_SESSION_MANAGER_KEY,
    AgentSessionManager,
    InMemoryAgentSessionStore,
)
from harness.agent.swarm import (
    SWARM_COORDINATOR_KEY,
    SwarmCoordinator,
    SwarmDAG,
    SwarmNode,
)
from harness.events.bus import EventBus
from harness.events.types import EventType, plugin_event
from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle
from harness.mcp.client_plugin import MCPClientPlugin
from harness.mcp.server import MCP_REGISTRY_KEY, MCPRegistry
from harness.plugins.catalog import PluginCatalog
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry
from harness.ui.server import create_app


@pytest.mark.asyncio
async def test_swarm_persistence_across_coordinator_instances() -> None:
    """Test that completed swarm runs persist into session manager and can be retrieved by fresh coordinators."""
    ctx = ServiceContext()
    event_bus = EventBus()
    store = InMemoryAgentSessionStore()
    sess_mgr = AgentSessionManager(store=store, event_bus=event_bus)
    ctx.provide(AGENT_SESSION_MANAGER_KEY, sess_mgr)

    coord_1 = SwarmCoordinator(context=ctx, event_bus=event_bus)

    dag = SwarmDAG()
    dag.add_node(
        SwarmNode(
            id="worker_a",
            role="worker",
            task="Compute value A",
            tools=["execute"],
        )
    )
    dag.add_node(
        SwarmNode(
            id="worker_b",
            role="worker",
            task="Compute value B",
            dependencies=["worker_a"],
            tools=["execute"],
        )
    )

    run_result = await coord_1.execute_dag(dag, objective="Compute combined value", run_id="swarm_test_101")
    assert run_result.run_id == "swarm_test_101"
    assert run_result.status == "completed"

    # Verify run exists in first coordinator
    assert coord_1.get_run("swarm_test_101") is not None

    # Now create fresh coordinator instance with same context/store
    coord_2 = SwarmCoordinator(context=ctx, event_bus=event_bus)
    assert coord_2.get_run("swarm_test_101") is None  # In-memory dict is fresh

    # Async retrieval falls back to session manager
    retrieved = await coord_2.get_run_async("swarm_test_101")
    assert retrieved is not None
    assert isinstance(retrieved, dict)
    assert retrieved["run_id"] == "swarm_test_101"
    assert retrieved["status"] == "completed"

    # Async listing includes stored swarm runs
    all_runs = await coord_2.list_runs_async()
    assert len(all_runs) >= 1
    assert any(r.get("run_id") == "swarm_test_101" for r in all_runs)


@pytest.mark.asyncio
async def test_swarm_run_convenience_method() -> None:
    """Test SwarmCoordinator.run_swarm convenience helper."""
    ctx = ServiceContext()
    coord = SwarmCoordinator(context=ctx)

    res = await coord.run_swarm("Auto-decompose objective test", run_id="swarm_auto_1")
    assert res.run_id == "swarm_auto_1"
    assert res.status == "completed"
    assert "synthesizer" in res.node_results or len(res.node_results) >= 1


@pytest.mark.asyncio
async def test_ui_server_swarm_rest_endpoints() -> None:
    """Test UI REST API endpoints for swarm status, listing, retrieval, execution tree, and execution."""
    ctx = ServiceContext()
    event_bus = EventBus()
    store = InMemoryAgentSessionStore()
    sess_mgr = AgentSessionManager(store=store, event_bus=event_bus)
    ctx.provide(AGENT_SESSION_MANAGER_KEY, sess_mgr)

    coord = SwarmCoordinator(context=ctx, event_bus=event_bus)
    ctx.provide(SWARM_COORDINATOR_KEY, coord)

    # Seed a swarm run
    await coord.run_swarm("API Swarm Task", run_id="swarm_api_run_1")

    lc = PluginLifecycle(ctx, event_bus)
    app = create_app(ctx, lc, event_bus)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Swarm status
        resp_status = await client.get("/api/swarm/status")
        assert resp_status.status_code == 200
        data_status = resp_status.json()
        assert data_status["coordinator_available"] is True
        assert data_status["total_runs"] >= 1

        # 2. List swarm runs
        resp_runs = await client.get("/api/swarm/runs")
        assert resp_runs.status_code == 200
        data_runs = resp_runs.json()
        assert data_runs["total"] >= 1
        assert any(r["run_id"] == "swarm_api_run_1" for r in data_runs["runs"])

        # 3. Get single swarm run
        resp_single = await client.get("/api/swarm/runs/swarm_api_run_1")
        assert resp_single.status_code == 200
        data_single = resp_single.json()
        assert data_single["status"] == "ok"
        assert data_single["run"]["run_id"] == "swarm_api_run_1"

        # 4. Get swarm run tree
        resp_tree = await client.get("/api/swarm/runs/swarm_api_run_1/tree")
        assert resp_tree.status_code == 200
        data_tree = resp_tree.json()
        assert data_tree["status"] == "ok"
        assert "tree" in data_tree

        # 5. Trigger new swarm run via POST
        resp_post = await client.post(
            "/api/swarm/run",
            json={"objective": "Dynamically triggered task", "run_id": "swarm_api_run_2"},
        )
        assert resp_post.status_code == 200
        data_post = resp_post.json()
        assert data_post["status"] == "ok"
        assert data_post["result"]["run_id"] == "swarm_api_run_2"


@pytest.mark.asyncio
async def test_mcp_client_mirroring_resources_and_prompts() -> None:
    """Test that MCPClientPlugin mirrors external resources and prompts into MCPRegistry."""
    ctx = ServiceContext()
    tools = ToolRegistry()
    ctx.provide(TOOL_REGISTRY_KEY, tools)

    mcp_registry = MCPRegistry(tool_registry=tools, context=ctx)
    ctx.provide(MCP_REGISTRY_KEY, mcp_registry)

    # Subclass or mock MCPClientPlugin's RPC layer
    client_plugin = MCPClientPlugin("mock_server", command="echo", args=["test"])
    await client_plugin.on_load(ctx)

    # Mock _send_rpc responses
    async def _mock_rpc(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if method == "initialize":
            return {"result": {"protocolVersion": "2024-11-05"}}
        if method == "tools/list":
            return {
                "result": {
                    "tools": [
                        {
                            "name": "echo_tool",
                            "description": "Echo tool description",
                            "inputSchema": {"type": "object", "properties": {"msg": {"type": "string"}}},
                        }
                    ]
                }
            }
        if method == "resources/list":
            return {
                "result": {
                    "resources": [
                        {
                            "uri": "custom://docs/intro",
                            "name": "Intro Doc",
                            "description": "Introduction to the mock service",
                            "mimeType": "text/markdown",
                        }
                    ]
                }
            }
        if method == "resources/read":
            return {
                "result": {
                    "contents": [{"uri": params.get("uri"), "text": "# Hello from Mock Resource"}]
                }
            }
        if method == "prompts/list":
            return {
                "result": {
                    "prompts": [
                        {
                            "name": "generate_report",
                            "description": "Generates a mock report",
                            "arguments": [{"name": "topic", "description": "Topic", "required": True}],
                        }
                    ]
                }
            }
        if method == "prompts/get":
            topic = (params or {}).get("arguments", {}).get("topic", "default")
            return {
                "result": {
                    "messages": [
                        {"role": "user", "content": {"type": "text", "text": f"Report on {topic}"}}
                    ]
                }
            }
        return {"result": {}}

    client_plugin._send_rpc = _mock_rpc
    client_plugin._start_mcp_process = lambda: asyncio.sleep(0)  # type: ignore[assignment]
    client_plugin._stop_mcp_process = lambda: asyncio.sleep(0)  # type: ignore[assignment]

    await client_plugin.on_enable()

    # 1. Verify tools mounted
    assert tools.has_tool("mcp.mock_server.echo_tool")

    # 2. Verify resources mounted into MCPRegistry
    resources = mcp_registry.list_resources()
    assert any(r["uri"] == "custom://docs/intro" for r in resources)

    # Read mounted resource
    read_res = await mcp_registry.read_resource("custom://docs/intro")
    assert read_res is not None
    content, mime = read_res
    assert content == "# Hello from Mock Resource"
    assert mime == "text/markdown"

    # 3. Verify prompts mounted into MCPRegistry
    prompts = mcp_registry.list_prompts()
    assert any(p["name"] == "mcp.mock_server.generate_report" for p in prompts)

    # Get mounted prompt
    desc, messages = await mcp_registry.get_prompt("mcp.mock_server.generate_report", {"topic": "AI Safety"})  # type: ignore[misc]
    assert "generate_report" in desc or "mock report" in desc
    assert len(messages) >= 1
    assert "AI Safety" in str(messages[0]["content"])

    # 4. Unmount on disable
    await client_plugin.on_disable()
    assert not tools.has_tool("mcp.mock_server.echo_tool")
    resources_after = mcp_registry.list_resources()
    assert not any(r["uri"] == "custom://docs/intro" for r in resources_after)
    prompts_after = mcp_registry.list_prompts()
    assert not any(p["name"] == "mcp.mock_server.generate_report" for p in prompts_after)


@pytest.mark.asyncio
async def test_plugin_catalog_event_driven_invalidation(tmp_path: Path) -> None:
    """Test that PluginCatalog invalidates and refreshes caches upon EventBus lifecycle events."""
    event_bus = EventBus()
    catalog = PluginCatalog([tmp_path], event_bus=event_bus)

    # Create dummy plugin directory
    p_dir = tmp_path / "test_plugin"
    p_dir.mkdir()
    manifest_file = p_dir / "plugin.json"
    manifest_file.write_text('{"name": "test_plugin", "version": "1.0.0", "description": "Version 1"}')

    catalog.refresh()
    entry = catalog.get("test_plugin")
    assert entry is not None
    manifest = entry.get_manifest()
    assert manifest is not None
    assert manifest.version == "1.0.0"

    # Update file on disk
    manifest_file.write_text('{"name": "test_plugin", "version": "2.0.0", "description": "Version 2"}')

    # Emit reload event on bus
    evt = plugin_event(EventType.PLUGIN_RELOADED, "test_plugin")
    await event_bus.emit(evt)

    # Catalog cache is invalidated
    updated_entry = catalog.get("test_plugin")
    assert updated_entry is not None
    updated_manifest = updated_entry.get_manifest()
    assert updated_manifest is not None
    assert updated_manifest.version == "2.0.0"
