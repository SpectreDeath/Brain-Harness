"""Tests for SwarmCoordinator, SwarmDAG, TokenGovernor, and ConsensusEngine."""

from __future__ import annotations

import pytest

from harness.agent.swarm import (
    SWARM_COORDINATOR_KEY,
    ConsensusEngine,
    SwarmCoordinator,
    SwarmCoordinatorPlugin,
    SwarmDAG,
    SwarmNode,
    TokenGovernor,
)
from harness.events.bus import EventBus
from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle


@pytest.mark.unit
class TestSwarmDAGAndGovernance:
    def test_dag_topological_waves(self) -> None:
        dag = SwarmDAG()
        dag.add_node(SwarmNode(id="n1", role="researcher", task="Research"))
        dag.add_node(SwarmNode(id="n2a", role="worker", task="Work A", dependencies=["n1"]))
        dag.add_node(SwarmNode(id="n2b", role="worker", task="Work B", dependencies=["n1"]))
        dag.add_node(SwarmNode(id="n3", role="synthesizer", task="Synthesize", dependencies=["n2a", "n2b"]))

        waves = dag.get_execution_plan()
        assert len(waves) == 3
        assert waves[0] == ["n1"]
        assert set(waves[1]) == {"n2a", "n2b"}
        assert waves[2] == ["n3"]

    def test_dag_cycle_detection(self) -> None:
        dag = SwarmDAG()
        dag.add_node(SwarmNode(id="a", role="worker", task="Task A", dependencies=["b"]))
        dag.add_node(SwarmNode(id="b", role="worker", task="Task B", dependencies=["a"]))

        with pytest.raises(ValueError, match="Cycle detected"):
            dag.get_execution_plan()

    def test_token_governor_budgeting(self) -> None:
        gov = TokenGovernor(max_tokens=1000)
        assert gov.remaining_budget == 1000
        assert gov.is_exhausted() is False

        allocated = gov.allocate("agent_1", 400)
        assert allocated == 400
        gov.record_usage("agent_1", 400)
        assert gov.remaining_budget == 600

        gov.record_usage("agent_2", 600)
        assert gov.remaining_budget == 0
        assert gov.is_exhausted() is True

    def test_consensus_engine_tally(self) -> None:
        votes = [
            {"agent": "a1", "vote": "approve", "confidence": 0.9},
            {"agent": "a2", "vote": "approve", "confidence": 0.8},
            {"agent": "a3", "vote": "reject", "confidence": 0.7},
        ]
        tally = ConsensusEngine.tally(votes, threshold=0.66)
        assert tally["status"] == "ok"
        assert tally["approvals"] == 2
        assert tally["rejections"] == 1
        assert tally["consensus_reached"] is True
        assert tally["decision"] == "APPROVED"


@pytest.mark.unit
@pytest.mark.asyncio
class TestSwarmCoordinatorExecution:
    async def test_swarm_coordinator_plugin_lifecycle(self) -> None:
        ctx = ServiceContext()
        lifecycle = PluginLifecycle(ctx)

        plugin = SwarmCoordinatorPlugin()
        lifecycle.discover(plugin)
        await lifecycle.load(plugin.name)
        await lifecycle.validate(plugin.name)
        await lifecycle.enable(plugin.name)

        coord = ctx.require(SWARM_COORDINATOR_KEY)
        assert isinstance(coord, SwarmCoordinator)
        status = await coord.get_status()
        assert status["status"] == "ready"

    async def test_swarm_execution_with_custom_executor(self) -> None:
        ctx = ServiceContext()
        bus = EventBus()
        coord = SwarmCoordinator(context=ctx, event_bus=bus)

        dag = SwarmDAG()
        dag.add_node(SwarmNode(id="researcher", role="researcher", task="Find auth vulnerabilities"))
        dag.add_node(SwarmNode(id="critic", role="critic", task="Audit findings", dependencies=["researcher"]))
        dag.add_node(SwarmNode(id="synthesizer", role="synthesizer", task="Draft report", dependencies=["critic"]))

        def mock_executor(node: SwarmNode, upstream_ctx: dict) -> str:
            if node.id == "researcher":
                return "Found 2 CVEs in auth"
            if node.id == "critic":
                return f"Verified: {upstream_ctx['researcher']}"
            return f"Final: {upstream_ctx['critic']}"

        result = await coord.run_swarm(
            dag,
            max_total_tokens=50_000,
            custom_executor=mock_executor,
        )

        assert result.status == "completed"
        assert "Final: Verified: Found 2 CVEs in auth" in result.final_synthesis
        assert "researcher" in result.node_results
        assert "critic" in result.node_results
        assert "synthesizer" in result.node_results
        assert result.total_tokens > 0

    async def test_swarm_decompose_and_run(self) -> None:
        ctx = ServiceContext()
        coord = SwarmCoordinator(context=ctx)

        result = await coord.run_swarm(
            "Build secure microservices API architecture",
            max_total_tokens=10_000,
        )
        assert result.status == "completed"
        assert len(result.node_results) >= 4
