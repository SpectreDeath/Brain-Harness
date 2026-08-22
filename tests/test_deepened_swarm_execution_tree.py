"""Tests for deepened SwarmExecutionTree, critical path analysis, and subtree metrics."""

import pytest

from harness.agent.session import AgentSessionManager, InMemoryAgentSessionStore
from harness.agent.swarm import (
    SwarmCoordinator,
    SwarmDAG,
    SwarmExecutionTree,
    SwarmNode,
    SwarmNodeExecution,
)
from harness.kernel.context import ServiceContext


@pytest.mark.asyncio
async def test_swarm_execution_tree_model_and_critical_path() -> None:
    """Verify SwarmExecutionTree correctly computes longest critical path and bottlenecks."""
    nodes = {
        "A": SwarmNodeExecution(id="A", role="worker", task="A", duration=2.0, tokens_used=500),
        "B": SwarmNodeExecution(id="B", role="worker", task="B", dependencies=["A"], duration=5.0, tokens_used=1200),
        "C": SwarmNodeExecution(id="C", role="worker", task="C", dependencies=["A"], duration=1.0, tokens_used=300),
        "D": SwarmNodeExecution(id="D", role="worker", task="D", dependencies=["B", "C"], duration=3.0, tokens_used=800),
    }
    tree = SwarmExecutionTree(
        run_id="run_123",
        objective="Test Objective",
        status="completed",
        start_time=100.0,
        end_time=111.0,
        duration=11.0,
        total_tokens=2800,
        nodes=nodes,
    )

    crit_path = tree.calculate_critical_path()
    assert crit_path == ["A", "B", "D"]
    assert tree.critical_path_duration == 10.0

    bottlenecks = tree.calculate_bottlenecks(token_threshold=1000, duration_threshold=4.0)
    assert len(bottlenecks) == 1
    assert bottlenecks[0]["node_id"] == "B"

    mermaid_str = tree.to_mermaid_graph()
    assert "graph TD" in mermaid_str
    assert "A --> B" in mermaid_str
    assert "B --> D" in mermaid_str

    tree_dict = tree.to_dict()
    assert tree_dict["run_id"] == "run_123"
    assert tree_dict["critical_path"] == ["A", "B", "D"]


@pytest.mark.asyncio
async def test_swarm_coordinator_run_and_analyze() -> None:
    """Verify SwarmCoordinator produces execution tree and enables analyze_run."""
    ctx = ServiceContext()
    session_store = InMemoryAgentSessionStore()
    session_mgr = AgentSessionManager(store=session_store)
    from harness.agent.session import AGENT_SESSION_MANAGER_KEY
    ctx.provide(AGENT_SESSION_MANAGER_KEY, session_mgr)

    coord = SwarmCoordinator(context=ctx)

    dag = SwarmDAG()
    dag.add_node(SwarmNode(id="step1", role="researcher", task="Find data"))
    dag.add_node(SwarmNode(id="step2", role="developer", task="Build code", dependencies=["step1"]))

    def mock_executor(node: SwarmNode, upstream: dict) -> str:
        return f"Output for {node.id}"

    result = await coord.run_swarm(dag, custom_executor=mock_executor, run_id="test_swarm_001")
    assert result.status == "completed"
    assert result.execution_tree is not None
    assert "step1" in result.execution_tree.nodes
    assert "step2" in result.execution_tree.nodes
    assert len(result.execution_tree.waves) == 2

    # Analyze run
    analytics = coord.analyze_run("test_swarm_001")
    assert analytics is not None
    assert analytics["run_id"] == "test_swarm_001"
    assert "critical_path" in analytics
    assert analytics["nodes"]["step1"]["status"] == "completed"


@pytest.mark.asyncio
async def test_agent_session_subtree_metrics() -> None:
    """Verify AgentSessionManager computes recursive subtree rollups."""
    store = InMemoryAgentSessionStore()
    mgr = AgentSessionManager(store=store)

    await mgr.create_session("Parent Task", session_id="p1")
    await mgr.create_child_session("p1", "Child 1", session_id="c1")
    await mgr.create_child_session("p1", "Child 2", session_id="c2")

    await mgr.complete_session("c1", "Done 1", total_tokens=250)
    await mgr.complete_session("c2", "Done 2", total_tokens=350)
    await mgr.complete_session("p1", "Parent Done", total_tokens=100)

    metrics = await mgr.get_subtree_metrics("p1")
    assert metrics["total_sessions"] == 3
    assert metrics["total_tokens"] == 700
    assert metrics["completed_count"] == 3
    assert metrics["failed_count"] == 0

    tree = await mgr.get_session_tree("p1")
    assert tree is not None
    assert tree["subtree_metrics"]["total_tokens"] == 700
    assert tree["subtree_metrics"]["child_count"] == 2
