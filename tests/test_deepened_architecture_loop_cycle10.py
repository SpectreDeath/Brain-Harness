"""Tests for Deepened Architecture Loop — Cycle 10.

Verifies:
1. Dynamic EcosystemBridgeCatalog and EcosystemLocator bidirectional synchronization.
2. ASTFunctionInspector parameter extraction, schema typing, and dynamic tool mounting.
3. Slotted and frozen SessionTreeNode and SessionTreeSnapshot hierarchy and aggregations.
4. Backward compatibility across CLI commands and diagnostic reports.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import pytest

from harness.agent.session import (
    AgentSession,
    AgentSessionManager,
    InMemoryAgentSessionStore,
    SessionTreeNode,
    SessionTreeSnapshot,
)
from harness.agent.base import AgentStep
from harness.bridges.base import (
    BridgeCapability,
    EcosystemBridgeCatalog,
    EcosystemBridgePlugin,
)
from harness.bridges.locator import BridgeDiagnosticReport, EcosystemLocator
from harness.commands.bridges import check_bridge_status_cmd, list_bridges_cmd
from harness.creator.dynamic import (
    ASTFunctionInspector,
    DynamicPluginBuilder,
    DynamicPythonPlugin,
    FunctionSignatureMetadata,
)
from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistryPlugin


# Mock bridge plugin for dynamic registration testing
class MockDynamicBridgePlugin(EcosystemBridgePlugin[Any]):
    project_name = "mock-dynamic-peer"
    env_var = "MOCK_DYNAMIC_PEER_PATH"
    service_key = ServiceKey("service.mock_dynamic_peer")
    capabilities = [BridgeCapability.CODE_EXECUTION, BridgeCapability.EPISTEMIC_AUDIT]

    @property
    def name(self) -> str:
        return "mock.dynamic.peer"

    @property
    def version(self) -> str:
        return "0.1.0"


@pytest.mark.unit
class TestCycle10EcosystemBridgeDeepening:
    """Test dynamic registration and synchronized diagnostic reporting for bridges."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self) -> Any:
        EcosystemBridgeCatalog.register(MockDynamicBridgePlugin)
        yield
        EcosystemBridgeCatalog.unregister("mock-dynamic-peer")

    def test_dynamic_bridge_registration_in_catalog_and_locator(self) -> None:
        # Register mock bridge in catalog
        EcosystemBridgeCatalog.register(MockDynamicBridgePlugin)


        assert EcosystemBridgeCatalog.get_bridge("mock-dynamic-peer") is MockDynamicBridgePlugin

        # Verify EcosystemLocator inspects dynamically registered bridge
        rep = EcosystemLocator.inspect_bridge("mock-dynamic-peer")
        assert rep.project_name == "mock-dynamic-peer"
        assert rep.env_var == "MOCK_DYNAMIC_PEER_PATH"
        assert "code_execution" in rep.capabilities
        assert "epistemic_audit" in rep.capabilities

        # Verify inspect_all includes mock bridge
        all_reps = EcosystemLocator.inspect_all()
        names = [r.project_name for r in all_reps]
        assert "mock-dynamic-peer" in names

    def test_catalog_diagnostic_reports(self) -> None:
        reports = EcosystemBridgeCatalog.get_diagnostic_reports()
        assert isinstance(reports, list)
        assert len(reports) >= 4
        names = [r.project_name for r in reports]
        assert "em-cubed" in names
        assert "mock-dynamic-peer" in names

    def test_bridge_commands_with_dynamic_bridge(self) -> None:
        bridges = list_bridges_cmd()
        names = [b["project_name"] for b in bridges]
        assert "mock-dynamic-peer" in names

        status_single = check_bridge_status_cmd("mock-dynamic-peer")
        assert status_single["status"] == "ok"
        assert status_single["bridge"]["project_name"] == "mock-dynamic-peer"
        assert "epistemic_audit" in status_single["bridge"]["capabilities"]


@pytest.mark.unit
class TestCycle10DynamicASTSynthesisDeepening:
    """Test ASTFunctionInspector, schema extraction, and dynamic tool mounting."""

    def test_ast_function_inspector_parameter_extraction(self) -> None:

        code = '''
def analyze_data(query: str, limit: int = 10, flags: list[str] | None = None) -> dict:
    """Perform data analysis with query and filtering flags."""
    return {"query": query, "limit": limit}

async def async_fetch(url: str, timeout: float = 30.0) -> str:
    """Fetch remote content asynchronously."""
    return url
'''
        metadata = ASTFunctionInspector.inspect_ast(code)
        assert "analyze_data" in metadata
        assert "async_fetch" in metadata

        fn1 = metadata["analyze_data"]
        assert fn1.name == "analyze_data"
        assert "Perform data analysis" in fn1.docstring
        assert fn1.is_async is False
        assert fn1.required == ["query"]
        assert fn1.parameters["query"]["type"] == "string"
        assert fn1.parameters["limit"]["type"] == "integer"
        assert fn1.parameters["limit"]["default"] == 10
        assert fn1.parameters["flags"]["type"] == "array"

        fn2 = metadata["async_fetch"]
        assert fn2.is_async is True
        assert fn2.parameters["timeout"]["type"] == "number"
        assert fn2.parameters["timeout"]["default"] == 30.0

        schema1 = fn1.to_parameters_schema()
        assert schema1["type"] == "object"
        assert "query" in schema1["properties"]
        assert schema1["required"] == ["query"]

    @pytest.mark.asyncio
    async def test_dynamic_python_plugin_with_ast_tool_specs(self) -> None:

        code = '''
def multiply_numbers(a: int, b: int = 5) -> int:
    """Multiply two integers together."""
    return a * b
'''
        plugin = DynamicPluginBuilder.from_code("dynamic-mult", code)

        ctx = ServiceContext()
        tools_plugin = ToolRegistryPlugin()
        await tools_plugin.on_load(ctx)

        await plugin.on_load(ctx)
        await plugin.on_enable()

        tool_reg = ctx.require(TOOL_REGISTRY_KEY)
        assert "multiply_numbers" in tool_reg

        spec = tool_reg.get("multiply_numbers")
        assert spec is not None
        assert "Multiply two integers" in spec.description
        assert spec.parameters_schema.get("properties", {}).get("a", {}).get("type") == "integer"
        assert spec.parameters_schema.get("properties", {}).get("b", {}).get("default") == 5
        assert spec.parameters_schema.get("required") == ["a"]

        res = await tool_reg.invoke("multiply_numbers", {"a": 7, "b": 3})
        assert res == {"status": "ok", "result": 21}

        await plugin.on_disable()
        assert "multiply_numbers" not in tool_reg


@pytest.mark.unit
@pytest.mark.asyncio
class TestCycle10SessionTreeSnapshotDeepening:
    """Test slotted SessionTreeNode and SessionTreeSnapshot hierarchy aggregation."""

    async def test_session_tree_snapshot_construction(self) -> None:
        store = InMemoryAgentSessionStore()
        manager = AgentSessionManager(store=store)

        # Create root session
        root = await manager.create_session("Root task: orchestrate multi-agent workflow", session_id="root_1")
        root.total_tokens = 150
        root.add_step(AgentStep(step_number=1, thought="Planning child tasks", action="delegate"))
        await store.save(root)

        # Create child session 1
        c1 = await manager.create_child_session("root_1", "Child task 1: fetch data", session_id="child_1")
        c1.total_tokens = 200
        c1.add_step(AgentStep(step_number=1, thought="Fetching", action="fetch"))
        c1.mark_completed("Data fetched", total_tokens=200)
        await store.save(c1)

        # Create child session 2
        c2 = await manager.create_child_session("root_1", "Child task 2: analyze data", session_id="child_2")
        c2.total_tokens = 350
        c2.add_step(AgentStep(step_number=1, thought="Analyzing", action="analyze"))
        c2.mark_completed("Analysis done", total_tokens=350)
        await store.save(c2)

        # Complete root
        root.mark_completed("Workflow complete", total_tokens=150)
        await store.save(root)

        # Retrieve slotted SessionTreeSnapshot
        snapshot = await manager.get_tree_snapshot("root_1")
        assert snapshot is not None
        assert isinstance(snapshot, SessionTreeSnapshot)
        assert snapshot.total_sessions == 3
        assert snapshot.total_tokens == 700  # 150 + 200 + 350
        assert snapshot.total_steps == 3
        assert snapshot.completed_count == 3
        assert snapshot.failed_count == 0
        assert snapshot.max_depth == 1

        # Check root node
        root_node = snapshot.root
        assert isinstance(root_node, SessionTreeNode)
        assert root_node.session_id == "root_1"
        assert root_node.depth == 0
        assert root_node.subtree_tokens == 700
        assert len(root_node.children) == 2

        # Check child node properties
        child_nodes = {c.session_id: c for c in root_node.children}
        assert "child_1" in child_nodes
        assert child_nodes["child_1"].depth == 1
        assert child_nodes["child_1"].subtree_tokens == 200

        # Verify serialization
        snap_dict = snapshot.to_dict()
        assert snap_dict["total_sessions"] == 3
        assert snap_dict["total_tokens"] == 700
        assert len(snap_dict["root"]["children"]) == 2
