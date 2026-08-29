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
