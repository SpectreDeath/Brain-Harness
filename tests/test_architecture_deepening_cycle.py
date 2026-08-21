"""Unit and integration tests for Deepened Architecture Seams.

Tests:
    1. RuntimeIntrospector & RuntimeAdapter diagnostics seams
    2. SwarmCoordinator lifecycle, run history, and consensus tally
    3. MCPRegistry dynamic resource & prompt extensions
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from harness.agent.swarm import (
    ConsensusEngine,
    SwarmCoordinator,
    SwarmDAG,
    SwarmNode,
)
from harness.creator.introspection import RuntimeIntrospector
from harness.events.bus import EventBus
from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle
from harness.kernel.runtime import HarnessRuntime
from harness.mcp.protocol import MCPPrompt, MCPProtocolCodec, MCPResource
from harness.mcp.server import HarnessMCPServer, MCPRegistry
from harness.plugins.base import HarnessPlugin
from harness.services.tools import ToolRegistry, ToolSpec
from harness.ui.server import RuntimeAdapter, create_app


class MockToolPlugin(HarnessPlugin):
    name = "mock.test_plugin"
    version = "1.2.3"
    description = "Test plugin for diagnostics"

    async def on_load(self, ctx: ServiceContext) -> None:
        pass


@pytest.mark.unit
def test_runtime_introspector_diagnostics() -> None:
    ctx = ServiceContext()
    bus = EventBus()
    lifecycle = PluginLifecycle(ctx, bus)
    tools = ToolRegistry()

    plugin = MockToolPlugin()
    lifecycle.discover(plugin)

    introspector = RuntimeIntrospector(ctx, lifecycle, tools)
    status = introspector.get_status_report()
    assert status["plugins_count"] == 1
    assert "mock.test_plugin" in status["plugins"]

    sandboxes = introspector.get_sandboxes_report()
    assert len(sandboxes) == 1
    assert sandboxes[0]["plugin"] == "mock.test_plugin"
    assert sandboxes[0]["state"] == "discovered"
    assert sandboxes[0]["is_sandboxed"] is False

    guide_report = introspector.get_plugin_guide_report("mock.test_plugin")
    assert guide_report["status"] == "ok"
    assert guide_report["name"] == "mock.test_plugin"
    assert "Test plugin for diagnostics" in guide_report["description"]

    missing_guide = introspector.get_plugin_guide_report("nonexistent_plugin")
    assert missing_guide["status"] == "error"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_ui_runtime_adapter_and_endpoints() -> None:
    async with HarnessRuntime.create(db_path=":memory:") as runtime:
        adapter = RuntimeAdapter(runtime)
        introspector = adapter.get_introspector()
        assert introspector is not None

        catalog = adapter.get_catalog()
        assert isinstance(catalog, list)

        sandboxes = adapter.get_sandboxes()
        assert isinstance(sandboxes, list)

        app = create_app(runtime)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Catalog
            res = await client.get("/api/catalog")
            assert res.status_code == 200
            data = res.json()
            assert "catalog" in data

            # Sandboxes
            res = await client.get("/api/sandboxes")
            assert res.status_code == 200
            data = res.json()
            assert "sandboxes" in data

            # Graph
            res = await client.get("/api/graph")
            assert res.status_code == 200
            assert "graph TD" in res.json()["mermaid"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_swarm_coordinator_lifecycle_and_history() -> None:
    ctx = ServiceContext()
    bus = EventBus()
    coordinator = SwarmCoordinator(context=ctx, event_bus=bus)

    status_before = await coordinator.get_status()
    assert status_before["active_swarms"] == 0
    assert status_before["total_runs"] == 0

    dag = SwarmDAG()
    dag.add_node(SwarmNode(id="debater_1", role="debater", task="Vote on proposition"))
    dag.add_node(SwarmNode(id="debater_2", role="debater", task="Vote on proposition"))

    def mock_executor(node: SwarmNode, upstream: dict) -> dict:
        return {"vote": "approve", "confidence": 0.9, "rationale": f"{node.id} agrees"}

    result = await coordinator.run_swarm(
        dag,
        custom_executor=mock_executor,
        run_id="test_run_123",
    )

    assert result.run_id == "test_run_123"
    assert result.status == "completed"
    assert result.consensus is not None
    assert result.consensus["consensus_reached"] is True
    assert result.consensus["approvals"] == 2

    # Verify history
    fetched = coordinator.get_run("test_run_123")
    assert fetched is not None
    assert fetched.run_id == "test_run_123"

    runs = coordinator.list_runs()
    assert len(runs) == 1
    assert runs[0].run_id == "test_run_123"

    status_after = await coordinator.get_status()
    assert status_after["active_swarms"] == 0
    assert status_after["total_runs"] == 1
    assert status_after["last_run"]["run_id"] == "test_run_123"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_mcp_registry_and_server_extensibility() -> None:
    tools = ToolRegistry()
    registry = MCPRegistry(tools)

    # Register custom resource
    registry.register_resource(
        MCPResource(
            uri="harness://custom/data",
            name="Custom Data Source",
            description="Custom data source for testing",
            handler=lambda: {"key": "value_42"},
        )
    )

    # Register custom prompt
    registry.register_prompt(
        MCPPrompt(
            name="custom_audit",
            description="Run custom audit on target",
            arguments=[{"name": "target", "required": True}],
            template_handler=lambda args: [
                {"role": "user", "content": {"type": "text", "text": f"Audit {args.get('target')}"}}
            ],
        )
    )

    server = HarnessMCPServer(tools, registry=registry)

    # Test initialize
    init_res = await server.handle_request({"id": 1, "method": "initialize"})
    assert init_res["result"]["serverInfo"]["name"] == "harness-mcp"

    # Test resources/list
    res_list = await server.handle_request({"id": 2, "method": "resources/list"})
    uris = [r["uri"] for r in res_list["result"]["resources"]]
    assert "harness://custom/data" in uris
    assert "harness://system/status" in uris

    # Test resources/read
    res_read = await server.handle_request({
        "id": 3,
        "method": "resources/read",
        "params": {"uri": "harness://custom/data"},
    })
    assert res_read["result"]["contents"][0]["uri"] == "harness://custom/data"
    assert "value_42" in res_read["result"]["contents"][0]["text"]

    # Test prompts/list
    p_list = await server.handle_request({"id": 4, "method": "prompts/list"})
    prompt_names = [p["name"] for p in p_list["result"]["prompts"]]
    assert "custom_audit" in prompt_names
    assert "agent_task" in prompt_names

    # Test prompts/get
    p_get = await server.handle_request({
        "id": 5,
        "method": "prompts/get",
        "params": {"name": "custom_audit", "arguments": {"target": "kernel.context"}},
    })
    assert p_get["result"]["description"] == "Run custom audit on target"
    assert "Audit kernel.context" in p_get["result"]["messages"][0]["content"]["text"]
