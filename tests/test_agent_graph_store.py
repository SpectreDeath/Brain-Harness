"""Unit tests for AgentExecutionGraphService and thread DAG lifecycle."""

from __future__ import annotations

import pytest

from harness.services.agent_graph import (
    AGENT_GRAPH_STORE_KEY,
    AgentExecutionGraphService,
    DefaultAgentExecutionGraphService,
    ThreadSpawnStatus,
)


@pytest.mark.unit
def test_agent_graph_store_service_key() -> None:
    """Verify ServiceKey registration."""
    assert AGENT_GRAPH_STORE_KEY.name == "service.agent_graph_store"


@pytest.mark.unit
def test_register_and_spawn_threads() -> None:
    """Test thread DAG creation, parent-child links, and ASCII tree rendering."""
    svc = DefaultAgentExecutionGraphService()

    # Register root supervisor
    root = svc.register_thread(
        node_id="sup_1",
        role="supervisor",
        task="Orchestrate repository refactoring",
    )
    assert root.node_id == "sup_1"
    assert root.status == "open"

    # Spawn child workers
    w1 = svc.register_thread(
        node_id="worker_ast",
        role="worker",
        task="Extract AST definitions",
        parent_id="sup_1",
    )
    w2 = svc.register_thread(
        node_id="worker_lint",
        role="worker",
        task="Run syntax validation",
        parent_id="sup_1",
    )

    # Spawn sub-child
    w1_sub = svc.register_thread(
        node_id="worker_pagerank",
        role="calculator",
        task="Calculate PageRank graph weights",
        parent_id="worker_ast",
    )

    # Update statuses
    svc.update_thread_status("worker_pagerank", status="completed", tokens_used=500, completed=True)
    svc.update_thread_status("worker_ast", status="completed", tokens_used=1200, completed=True)
    svc.update_thread_status("worker_lint", status="completed", tokens_used=800, completed=True)
    svc.update_thread_status("sup_1", status="completed", tokens_used=300, completed=True)

    # Export graph
    export = svc.export_graph()
    assert export.status == "ok"
    assert export.total_nodes == 4
    assert export.total_edges == 3
    assert export.total_tokens_rollup == 2800

    # Verify ASCII tree formatting
    tree_text = export.formatted_ascii_tree
    assert "sup_1" in tree_text
    assert "worker_ast" in tree_text
    assert "worker_pagerank" in tree_text
    assert "worker_lint" in tree_text


@pytest.mark.asyncio
async def test_session_manager_graph_store_lifecycle() -> None:
    """Verify AgentSessionManager registers sessions and tracks status in AgentExecutionGraphService."""
    from harness.agent.session import AgentSessionManager, InMemoryAgentSessionStore
    from harness.kernel.context import ServiceContext

    context = ServiceContext()
    graph_svc = DefaultAgentExecutionGraphService()
    context.provide(AGENT_GRAPH_STORE_KEY, graph_svc)

    store = InMemoryAgentSessionStore()
    manager = AgentSessionManager(store=store, context=context)

    # 1. Create root session
    root_sess = await manager.create_session(task="Refactor core architecture", role="lead_architect")
    export = graph_svc.export_graph()
    assert root_sess.session_id in export.formatted_ascii_tree
    assert export.total_nodes == 1

    # 2. Create child session
    child_sess = await manager.create_session(
        task="Audit PR changes",
        role="code_reviewer",
        parent_session_id=root_sess.session_id,
    )
    export = graph_svc.export_graph()
    assert child_sess.session_id in export.formatted_ascii_tree
    assert export.total_nodes == 2
    assert export.total_edges == 1

    # 3. Complete child session
    await manager.complete_session(child_sess.session_id, final_answer="Review finished with zero issues")
    export_after_complete = graph_svc.export_graph()
    child_node = export_after_complete.nodes.get(child_sess.session_id)
    assert child_node is not None
    assert child_node.status == "completed"

    # 4. Fail root session
    await manager.fail_session(root_sess.session_id, error_message="Aborted by user")
    export_after_fail = graph_svc.export_graph()
    root_node = export_after_fail.nodes.get(root_sess.session_id)
    assert root_node is not None
    assert root_node.status == "failed"


@pytest.mark.asyncio
async def test_swarm_coordinator_graph_store_lifecycle() -> None:
    """Verify SwarmCoordinator registers swarm runs and node DAG in AgentExecutionGraphService."""
    from harness.agent.swarm import SwarmCoordinator, SwarmDAG, SwarmNode
    from harness.kernel.context import ServiceContext

    context = ServiceContext()
    graph_svc = DefaultAgentExecutionGraphService()
    context.provide(AGENT_GRAPH_STORE_KEY, graph_svc)

    coordinator = SwarmCoordinator(context=context)

    dag = SwarmDAG()
    dag.add_node(SwarmNode(id="scan", role="scanner", task="Scan directory"))
    dag.add_node(SwarmNode(id="synthesize", role="builder", task="Synthesize code", dependencies=["scan"]))

    def mock_executor(node: SwarmNode, upstream_ctx: dict) -> str:
        return f"Done {node.id}"

    result = await coordinator.run_swarm(dag, custom_executor=mock_executor)
    assert result.status == "completed"

    export = graph_svc.export_graph()
    assert export.total_nodes >= 3  # root swarm + 2 nodes
    assert "scan" in export.formatted_ascii_tree
    assert "synthesize" in export.formatted_ascii_tree

    scan_sid = f"{result.run_id}_scan"
    synth_sid = f"{result.run_id}_synthesize"
    scan_node = export.nodes.get(scan_sid)
    assert scan_node is not None
    assert scan_node.status == "completed"

    synth_node = export.nodes.get(synth_sid)
    assert synth_node is not None
    assert synth_node.status == "completed"


