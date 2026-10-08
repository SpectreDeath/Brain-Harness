"""Contract verification suite for deepened Swarm seams (Step 3E).

Validates:
1. Isolated submodule importability across all swarm modules.
2. Wave scheduler topological tiering and DAG cycle prevention.
3. Pluggable consensus strategies: BinaryThreshold, Borda, WeightedMajority, and tie handling.
4. Tree renderer Mermaid output generation.
5. Token governor isolation.
"""

from __future__ import annotations

import pytest


def test_all_swarm_submodule_independent_imports() -> None:
    """Verify all swarm submodules can be imported in complete isolation."""
    from harness.agent.swarm import models
    from harness.agent.swarm import governor
    from harness.agent.swarm import consensus
    from harness.agent.swarm import wave_scheduler
    from harness.agent.swarm import tree_renderer
    from harness.agent.swarm import coordinator
    from harness.agent.swarm import plugin

    assert hasattr(models, "SwarmNode")
    assert hasattr(models, "SwarmDAG")
    assert hasattr(governor, "TokenGovernor")
    assert hasattr(consensus, "ConsensusEngine")
    assert hasattr(consensus, "BordaConsensusStrategy")
    assert hasattr(consensus, "WeightedMajorityStrategy")
    assert hasattr(wave_scheduler, "SwarmWaveScheduler")
    assert hasattr(tree_renderer, "SwarmTreeRenderer")
    assert hasattr(coordinator, "SwarmCoordinator")
    assert hasattr(plugin, "SwarmCoordinatorPlugin")


def test_wave_scheduler_dependency_ordering() -> None:
    """Verify SwarmWaveScheduler correctly partitions a 3-tier synthetic DAG into execution waves."""
    from harness.agent.swarm.models import SwarmDAG, SwarmNode
    from harness.agent.swarm.wave_scheduler import SwarmWaveScheduler

    dag = SwarmDAG()
    dag.add_node(SwarmNode(id="root", role="planner", task="plan"))
    dag.add_node(SwarmNode(id="worker_a", role="researcher", task="research", dependencies=["root"]))
    dag.add_node(SwarmNode(id="worker_b", role="coder", task="code", dependencies=["root"]))
    dag.add_node(SwarmNode(id="final", role="synthesizer", task="synthesize", dependencies=["worker_a", "worker_b"]))

    scheduler = SwarmWaveScheduler()
    waves = scheduler.compute_waves(dag)

    assert len(waves) == 3
    assert waves[0] == ["root"]
    assert sorted(waves[1]) == ["worker_a", "worker_b"]
    assert waves[2] == ["final"]


def test_wave_scheduler_cycle_prevention() -> None:
    """Verify SwarmWaveScheduler rejects cyclic dependencies with ValueError."""
    from harness.agent.swarm.models import SwarmDAG, SwarmNode
    from harness.agent.swarm.wave_scheduler import SwarmWaveScheduler

    dag = SwarmDAG()
    dag.add_node(SwarmNode(id="a", role="worker", task="a", dependencies=["b"]))
    dag.add_node(SwarmNode(id="b", role="worker", task="b", dependencies=["a"]))

    scheduler = SwarmWaveScheduler()
    with pytest.raises(ValueError, match="Cycle detected"):
        scheduler.compute_waves(dag)


def test_binary_threshold_strategy_consensus() -> None:
    """Verify BinaryThresholdStrategy approves when ratio exceeds threshold."""
    from harness.agent.swarm.consensus import BinaryThresholdStrategy

    strategy = BinaryThresholdStrategy()
    votes = [
        {"vote": "approve", "confidence": 0.9},
        {"vote": "yes", "confidence": 0.85},
        {"vote": "1", "confidence": 0.8},
        {"vote": "reject", "confidence": 0.4},
    ]
    # 3 approves out of 4 = 0.75 >= 0.66 threshold
    res = strategy.evaluate(votes, threshold=0.66)
    assert res["status"] == "ok"
    assert res["total_votes"] == 4
    assert res["approvals"] == 3
    assert res["rejections"] == 1
    assert res["approval_ratio"] == 0.75
    assert res["consensus_reached"] is True
    assert res["decision"] == "APPROVED"


def test_borda_consensus_strategy() -> None:
    """Verify BordaConsensusStrategy assigns rank points and elects highest-scored candidate."""
    from harness.agent.swarm.consensus import BordaConsensusStrategy

    strategy = BordaConsensusStrategy()
    votes = [
        {"voter": "v1", "ranked_choices": ["option_A", "option_B", "option_C"]},  # A:2, B:1, C:0
        {"voter": "v2", "ranked_choices": ["option_A", "option_C", "option_B"]},  # A:2, C:1, B:0
        {"voter": "v3", "ranked_choices": ["option_B", "option_A", "option_C"]},  # B:2, A:1, C:0
    ]
    # Total scores: A = 2+2+1 = 5, B = 1+0+2 = 3, C = 0+1+0 = 1
    res = strategy.evaluate(votes)
    assert res["status"] == "ok"
    assert res["consensus_reached"] is True
    assert res["winner"] == "option_A"
    assert res["top_score"] == 5.0
    assert res["decision"] == "option_A"
    assert res["is_tie"] is False


def test_weighted_majority_consensus() -> None:
    """Verify WeightedMajorityStrategy aggregates confidence weights per candidate."""
    from harness.agent.swarm.consensus import WeightedMajorityStrategy

    strategy = WeightedMajorityStrategy()
    votes = [
        {"choice": "blue", "confidence": 0.9, "weight": 2.0},   # 1.8
        {"choice": "blue", "confidence": 0.8, "weight": 1.0},   # 0.8 -> blue total = 2.6
        {"choice": "red", "confidence": 0.95, "weight": 2.0},   # 1.9 -> red total = 1.9
    ]
    res = strategy.evaluate(votes)
    assert res["status"] == "ok"
    assert res["consensus_reached"] is True
    assert res["winner"] == "blue"
    assert res["top_weight"] == 2.6
    assert res["is_tie"] is False


def test_tie_handling_in_consensus() -> None:
    """Verify that ties result in NO_CONSENSUS decision without crashes."""
    from harness.agent.swarm.consensus import BordaConsensusStrategy, WeightedMajorityStrategy

    # Borda tie
    borda = BordaConsensusStrategy()
    borda_votes = [
        {"ranked_choices": ["cand1", "cand2"]},  # cand1: 1, cand2: 0
        {"ranked_choices": ["cand2", "cand1"]},  # cand2: 1, cand1: 0
    ]
    borda_res = borda.evaluate(borda_votes)
    assert borda_res["status"] == "ok"
    assert borda_res["consensus_reached"] is False
    assert borda_res["decision"] == "NO_CONSENSUS"
    assert borda_res["is_tie"] is True

    # Weighted majority tie
    wm = WeightedMajorityStrategy()
    wm_votes = [
        {"choice": "alpha", "confidence": 1.0, "weight": 1.0},
        {"choice": "beta", "confidence": 1.0, "weight": 1.0},
    ]
    wm_res = wm.evaluate(wm_votes)
    assert wm_res["status"] == "ok"
    assert wm_res["consensus_reached"] is False
    assert wm_res["decision"] == "NO_CONSENSUS"
    assert wm_res["is_tie"] is True


def test_tree_renderer_mermaid_output() -> None:
    """Verify SwarmTreeRenderer generates valid Mermaid DAG syntax with nodes and edges."""
    from harness.agent.swarm.models import SwarmExecutionTree, SwarmNodeExecution
    from harness.agent.swarm.tree_renderer import SwarmTreeRenderer

    node_a = SwarmNodeExecution(
        id="step_a",
        role="fetcher",
        task="fetch data",
        status="completed",
        duration=1.2,
        tokens_used=250,
    )
    node_b = SwarmNodeExecution(
        id="step_b",
        role="analyzer",
        task="analyze data",
        dependencies=["step_a"],
        status="completed",
        duration=2.5,
        tokens_used=500,
    )

    tree = SwarmExecutionTree(
        run_id="run_123",
        objective="test render",
        status="completed",
        nodes={"step_a": node_a, "step_b": node_b},
    )

    mermaid_str = SwarmTreeRenderer.render_mermaid(tree)
    assert "graph TD" in mermaid_str
    assert 'step_a["step_a [fetcher]' in mermaid_str
    assert 'step_b["step_b [analyzer]' in mermaid_str
    assert "step_a --> step_b" in mermaid_str

    ascii_str = SwarmTreeRenderer.render_ascii(tree)
    assert "run_123" in ascii_str
    assert "step_a" in ascii_str
    assert "step_b" in ascii_str


def test_token_governor_isolation() -> None:
    """Verify TokenGovernor tracks bounds, grants allocations, and detects exhaustion."""
    from harness.agent.swarm.governor import TokenGovernor

    gov = TokenGovernor(max_tokens=5_000)
    assert gov.remaining_budget == 5_000
    assert not gov.is_exhausted()

    # Allocate 3,000
    a1 = gov.allocate("agent_x", 3_000)
    assert a1 == 3_000
    gov.record_usage("agent_x", 3_000)
    assert gov.remaining_budget == 2_000

    # Request more than remaining
    a2 = gov.allocate("agent_y", 4_000)
    assert a2 == 2_000
    gov.record_usage("agent_y", 2_000)
    assert gov.remaining_budget == 0
    assert gov.is_exhausted()

    stats = gov.get_stats()
    assert stats["max_tokens"] == 5_000
    assert stats["tokens_consumed"] == 5_000
    assert stats["remaining_budget"] == 0
    assert stats["is_exhausted"] is True
    assert stats["usage_by_agent"]["agent_x"] == 3_000
    assert stats["usage_by_agent"]["agent_y"] == 2_000
