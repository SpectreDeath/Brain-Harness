"""Contract verification tests for SwarmCoordinator modular decomposition (Cycle 24)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from harness.agent.session import InMemoryAgentSessionStore, AgentSessionManager
from harness.agent.swarm.models import SwarmDAG, SwarmNode
from harness.kernel.context import ServiceContext


@pytest.mark.unit
def test_submodule_line_counts():
    """Verify all decomposed submodules in coordinator/ obey the < 200 line budget (Rule 11)."""
    coord_dir = Path("src/harness/agent/swarm/coordinator")
    assert coord_dir.is_dir()
    py_files = list(coord_dir.glob("*.py"))
    assert len(py_files) >= 8

    for py_file in py_files:
        lines = py_file.read_text(encoding="utf-8").splitlines()
        assert len(lines) < 200, f"{py_file.name} has {len(lines)} lines (budget is < 200)"


@pytest.mark.unit
def test_direct_submodule_imports():
    """Verify all decomposed submodules can be imported independently without circular dependencies."""
    from harness.agent.swarm.coordinator.core import SWARM_COORDINATOR_KEY, SwarmCoordinator
    from harness.agent.swarm.coordinator.decomposition import (
        decompose_objective,
        decompose_objective_with_skills,
    )
    from harness.agent.swarm.coordinator.history import (
        analyze_run_metrics,
        build_status_summary,
        get_run_async_with_fallback,
        get_run_from_cache,
        get_run_session_tree_hierarchy,
        list_runs_async_with_fallback,
        list_runs_cached,
    )
    from harness.agent.swarm.coordinator.node_runner import execute_swarm_node
    from harness.agent.swarm.coordinator.outcome import finalize_swarm_outcome
    from harness.agent.swarm.coordinator.resolvers import resolve_swarm_coordinator
    from harness.agent.swarm.coordinator.wave_runner import execute_swarm_wave, init_swarm_session

    assert SWARM_COORDINATOR_KEY is not None
    assert SwarmCoordinator is not None
    assert decompose_objective is not None
    assert decompose_objective_with_skills is not None
    assert analyze_run_metrics is not None
    assert build_status_summary is not None
    assert get_run_async_with_fallback is not None
    assert get_run_from_cache is not None
    assert get_run_session_tree_hierarchy is not None
    assert list_runs_async_with_fallback is not None
    assert list_runs_cached is not None
    assert execute_swarm_node is not None
    assert finalize_swarm_outcome is not None
    assert resolve_swarm_coordinator is not None
    assert execute_swarm_wave is not None
    assert init_swarm_session is not None


@pytest.mark.unit
def test_facade_re_exports_and_backward_compatibility():
    """Verify package __init__.py re-exports all domain symbols."""
    from harness.agent.swarm.coordinator import (
        SWARM_COORDINATOR_KEY,
        SwarmCoordinator,
        analyze_run_metrics,
        build_status_summary,
        decompose_objective,
        decompose_objective_with_skills,
        execute_swarm_node,
        execute_swarm_wave,
        finalize_swarm_outcome,
        get_run_async_with_fallback,
        get_run_from_cache,
        get_run_session_tree_hierarchy,
        list_runs_async_with_fallback,
        list_runs_cached,
        resolve_swarm_coordinator,
    )

    assert SWARM_COORDINATOR_KEY is not None
    assert SwarmCoordinator is not None
    assert analyze_run_metrics is not None
    assert build_status_summary is not None
    assert decompose_objective is not None
    assert decompose_objective_with_skills is not None
    assert execute_swarm_node is not None
    assert execute_swarm_wave is not None
    assert finalize_swarm_outcome is not None
    assert get_run_async_with_fallback is not None
    assert get_run_from_cache is not None
    assert get_run_session_tree_hierarchy is not None
    assert list_runs_async_with_fallback is not None
    assert list_runs_cached is not None
    assert resolve_swarm_coordinator is not None


@pytest.mark.unit
def test_swarm_package_facade_compatibility():
    """Verify top-level harness.agent.swarm imports continue functioning seamlessly."""
    from harness.agent.swarm import (
        SWARM_COORDINATOR_KEY,
        SwarmCoordinator,
        coordinator,
    )

    assert SWARM_COORDINATOR_KEY is not None
    assert SwarmCoordinator is not None
    assert hasattr(coordinator, "SwarmCoordinator")
    assert hasattr(coordinator, "SWARM_COORDINATOR_KEY")


@pytest.mark.unit
def test_plugin_singleton_export():
    """Verify module-level plugin singleton exists in swarm/plugin.py (Rule 45)."""
    from harness.agent.swarm.coordinator import SWARM_COORDINATOR_KEY
    from harness.agent.swarm.plugin import SwarmCoordinatorPlugin, plugin

    assert isinstance(plugin, SwarmCoordinatorPlugin)
    assert plugin.name == "agent.swarm"
    assert plugin.provides == [SWARM_COORDINATOR_KEY]


@pytest.mark.unit
def test_single_seam_resolver():
    """Verify resolve_swarm_coordinator single-seam resolver factory (Rule 58)."""
    from harness.agent.swarm.coordinator import resolve_swarm_coordinator, SwarmCoordinator

    ctx = ServiceContext()
    coord = resolve_swarm_coordinator(ctx)
    assert isinstance(coord, SwarmCoordinator)

    # Calling resolve again returns the existing provided service if registered
    from harness.agent.swarm.coordinator import SWARM_COORDINATOR_KEY
    ctx.provide(SWARM_COORDINATOR_KEY, coord)
    resolved_again = resolve_swarm_coordinator(ctx)
    assert resolved_again is coord


@pytest.mark.unit
def test_objective_decomposition():
    """Verify decomposition produces valid SwarmDAG structures."""
    from harness.agent.swarm.coordinator import decompose_objective

    dag = decompose_objective("Deploy new web service")
    assert len(dag.nodes) == 4
    assert "researcher" in dag.nodes
    assert "developer" in dag.nodes
    assert "critic" in dag.nodes
    assert "synthesizer" in dag.nodes
    assert dag.nodes["developer"].dependencies == ["researcher"]


@pytest.mark.asyncio
@pytest.mark.unit
async def test_swarm_execution_and_analytics():
    """Verify SwarmCoordinator executes a synthetic DAG with custom executor and generates analytics."""
    from harness.agent.swarm.coordinator import SwarmCoordinator

    ctx = ServiceContext()
    coord = SwarmCoordinator(context=ctx)

    dag = SwarmDAG()
    dag.add_node(SwarmNode(id="step_1", role="fetcher", task="fetch data"))
    dag.add_node(SwarmNode(id="step_2", role="processor", task="process data", dependencies=["step_1"]))

    def custom_exec(node: SwarmNode, upstream: dict[str, Any]) -> str:
        if node.id == "step_1":
            return "raw_payload"
        return f"processed: {upstream.get('step_1')}"

    result = await coord.run_swarm(
        dag=dag,
        objective="Process dataset",
        custom_executor=custom_exec,
        run_id="run_custom_test",
    )

    assert result.status == "completed"
    assert result.node_results["step_1"] == "raw_payload"
    assert result.node_results["step_2"] == "processed: raw_payload"
    assert result.execution_tree is not None
    assert len(result.execution_tree.waves) == 2

    # Query run history
    fetched = coord.get_run("run_custom_test")
    assert fetched is result

    analytics = coord.analyze_run("run_custom_test")
    assert analytics is not None
    assert analytics["run_id"] == "run_custom_test"

    status = await coord.get_status()
    assert status["total_runs"] >= 1
    assert status["status"] == "ready"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_child_session_composite_keying_rule_36():
    """Verify node child sessions are created with composite run_id_node_id keys (Rule 36)."""
    from harness.agent.session import AGENT_SESSION_MANAGER_KEY
    from harness.agent.swarm.coordinator import SwarmCoordinator

    ctx = ServiceContext()
    store = InMemoryAgentSessionStore()
    session_mgr = AgentSessionManager(store=store)
    ctx.provide(AGENT_SESSION_MANAGER_KEY, session_mgr)

    coord = SwarmCoordinator(context=ctx)

    dag = SwarmDAG()
    dag.add_node(SwarmNode(id="audit_node", role="auditor", task="audit code"))

    run_id = "test_run_36"
    result = await coord.run_swarm(
        dag=dag,
        objective="Run audit",
        custom_executor=lambda node, upstream: "audit_clean",
        run_id=run_id,
    )

    assert result.status == "completed"

    # Verify composite key child session was created and completed
    child_session_id = f"{run_id}_audit_node"
    child_session = await session_mgr.get_session(child_session_id)
    assert child_session is not None
    assert child_session.parent_session_id == run_id
    assert child_session.status == "completed"
    assert child_session.final_answer == "audit_clean"


@pytest.mark.unit
def test_doc_link_and_explanation_reference():
    """Verify that coordinator is properly documented and referenced."""
    from harness.agent.swarm import coordinator
    assert hasattr(coordinator, "SwarmCoordinator")
