"""Characterization test suite for the decomposed Swarm architecture.

Verifies:
1. Isolated submodule importability (models, governor, consensus, coordinator, plugin).
2. Backward-compatible package re-exports from harness.agent.swarm.
3. Token governor, consensus engine, DAG planning, and coordinator lifecycle.
"""

from __future__ import annotations

import pytest

from harness.kernel.context import ServiceContext


def test_submodule_isolated_imports() -> None:
    """Verify each decomposed submodule can be imported in isolation."""
    from harness.agent.swarm import models
    from harness.agent.swarm import governor
    from harness.agent.swarm import consensus
    from harness.agent.swarm import coordinator
    from harness.agent.swarm import plugin

    assert hasattr(models, "SwarmNode")
    assert hasattr(models, "SwarmDAG")
    assert hasattr(models, "SwarmExecutionTree")
    assert hasattr(governor, "TokenGovernor")
    assert hasattr(consensus, "ConsensusEngine")
    assert hasattr(coordinator, "SwarmCoordinator")
    assert hasattr(coordinator, "SWARM_COORDINATOR_KEY")
    assert hasattr(plugin, "SwarmCoordinatorPlugin")


def test_package_re_exports() -> None:
    """Verify harness.agent.swarm re-exports all public symbols."""
    import harness.agent.swarm as swarm

    expected_symbols = [
        "SwarmDAG",
        "SwarmExecutionTree",
        "SwarmNode",
        "SwarmNodeExecution",
        "SwarmTaskResult",
        "SwarmWaveMetrics",
        "ConsensusEngine",
        "TokenGovernor",
        "SwarmCoordinator",
        "SwarmCoordinatorPlugin",
        "SWARM_COORDINATOR_KEY",
        "AGENT_CONTEXT_OPTIMIZER_KEY",
        "AGENT_GRAPH_STORE_KEY",
        "AGENT_SESSION_MANAGER_KEY",
        "AgentContextOptimizer",
        "AgentExecutionGraphService",
        "AgentSessionManager",
        "AgentTaskResult",
        "ThreadSpawnStatus",
    ]
    for sym in expected_symbols:
        assert hasattr(swarm, sym), f"Missing symbol in harness.agent.swarm: {sym}"


def test_token_governor_allocation_and_stats() -> None:
    """Verify TokenGovernor tracks and bounds usage cleanly."""
    from harness.agent.swarm.governor import TokenGovernor

    gov = TokenGovernor(max_tokens=1_000)
    assert gov.remaining_budget == 1_000
    assert not gov.is_exhausted()

    granted = gov.allocate("worker1", 600)
    assert granted == 600

    gov.record_usage("worker1", 600)
    assert gov.remaining_budget == 400

    granted_next = gov.allocate("worker2", 500)
    assert granted_next == 400

    gov.record_usage("worker2", 400)
    assert gov.remaining_budget == 0
    assert gov.is_exhausted()


def test_consensus_engine_supermajority() -> None:
    """Verify ConsensusEngine tallies supermajority decisions."""
    from harness.agent.swarm.consensus import ConsensusEngine

    votes = [
        {"voter": "agent1", "vote": "approve", "confidence": 0.9},
        {"voter": "agent2", "vote": "approve", "confidence": 0.8},
        {"voter": "agent3", "vote": "reject", "confidence": 0.5},
    ]
    tally = ConsensusEngine.tally(votes, threshold=0.66)
    assert tally["status"] == "ok"
    assert tally["total_votes"] == 3
    assert tally["approvals"] == 2
    assert tally["rejections"] == 1
    assert tally["consensus_reached"] is True
    assert tally["decision"] == "APPROVED"


def test_swarm_dag_cycle_and_waves() -> None:
    """Verify SwarmDAG builds dependency waves and detects cycles."""
    from harness.agent.swarm.models import SwarmDAG, SwarmNode

    dag = SwarmDAG()
    dag.add_node(SwarmNode(id="n1", role="fetcher", task="fetch"))
    dag.add_node(SwarmNode(id="n2", role="processor", task="process", dependencies=["n1"]))
    dag.add_node(SwarmNode(id="n3", role="synthesizer", task="synthesize", dependencies=["n2"]))

    waves = dag.get_execution_plan()
    assert waves == [["n1"], ["n2"], ["n3"]]

    # Cycle test
    dag.nodes["n1"].dependencies.append("n3")
    with pytest.raises(ValueError, match="Cycle detected"):
        dag.get_execution_plan()


@pytest.mark.asyncio
async def test_swarm_coordinator_plugin_lifecycle() -> None:
    """Verify SwarmCoordinatorPlugin provides SWARM_COORDINATOR_KEY in IoC context."""
    from harness.agent.swarm.coordinator import SWARM_COORDINATOR_KEY, SwarmCoordinator
    from harness.agent.swarm.plugin import SwarmCoordinatorPlugin

    ctx = ServiceContext()
    plugin = SwarmCoordinatorPlugin()
    await plugin.on_load(ctx)

    coordinator = ctx.require(SWARM_COORDINATOR_KEY)
    assert isinstance(coordinator, SwarmCoordinator)
    status = await coordinator.get_status()
    assert status["status"] == "ready"
