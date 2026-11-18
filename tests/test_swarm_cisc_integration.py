"""Contract tests wiring CISC confidence-weighted voting into Swarm ConsensusEngine & SwarmCoordinator."""

from __future__ import annotations

from typing import Any

import pytest

from harness.agent.swarm.consensus import ConsensusEngine, WeightedMajorityStrategy
from harness.agent.swarm.coordinator.core import SwarmCoordinator
from harness.agent.swarm.models import SwarmDAG, SwarmNode
from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.uncertainty_guard.main import plugin as guard_plugin


@pytest.mark.unit
def test_consensus_engine_cisc_softmax_overrides_low_confidence_plurality() -> None:
    """CISC softmax consensus lets high-confidence minority beat noisy low-confidence majority."""
    votes = [
        {"choice": "draft_a", "confidence": 0.05},
        {"choice": "draft_a", "confidence": 0.10},
        {"choice": "draft_a", "confidence": 0.0},
        {"choice": "draft_b", "confidence": 0.96},
        {"choice": "draft_b", "confidence": 0.94},
    ]
    res = ConsensusEngine.evaluate_cisc_consensus(votes, normalization="softmax", temperature=3.0)
    assert res["status"] == "ok"
    assert res["winner"] == "draft_b"
    assert res["decision"] == "draft_b"
    assert res["consensus_reached"] is True
    assert res["valid_trace_count"] == 5
    assert res["source"] == "builtin_cisc"

    # WeightedMajorityStrategy preserves raw behavior by default
    raw = WeightedMajorityStrategy().evaluate(votes)
    assert raw["winner"] == "draft_b"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_swarm_coordinator_resolves_cisc_via_uncertainty_guard_ioc() -> None:
    """SwarmCoordinator resolves UNCERTAINTY_GUARD_SERVICE_KEY and aggregates node choice votes."""
    ctx = ServiceContext()
    await guard_plugin.on_load(ctx)
    coord = SwarmCoordinator(context=ctx)

    dag = SwarmDAG()
    for nid in ("w1", "w2", "w3", "w4"):
        dag.add_node(SwarmNode(id=nid, role="reasoner", task=f"trace-{nid}"))

    async def executor(node: SwarmNode, deps: dict[str, Any]) -> dict[str, Any]:
        if node.id in ("w1", "w2", "w3"):
            return {"choice": "hallucinated_path", "confidence": 0.05}
        return {"choice": "verified_path", "confidence": 0.98, "weight": 1.0}

    result = await coord.run_swarm(
        dag=dag,
        objective="Select highest-confidence trace",
        custom_executor=executor,
    )
    assert result.status == "completed"
    assert result.consensus is not None
    assert result.consensus["winner"] == "verified_path"
    assert result.consensus["consensus_reached"] is True
    assert result.consensus["source"] == "service.uncertainty_guard"

    await guard_plugin.on_unload(ctx)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_evaluate_cisc_consensus_ki_provenance_weighting() -> None:
    """ki_verification_map scales CISC votes by verified/unverified/none provenance multipliers."""
    dispute_votes = [
        {"choice": "ungrounded", "confidence": 0.85, "ki_id": None},
        {"choice": "ungrounded", "confidence": 0.85, "ki_id": None},
        {"choice": "ungrounded", "confidence": 0.85},
        {"choice": "verified", "confidence": 0.85, "ki_id": "ki_verified"},
        {"choice": "verified", "confidence": 0.85, "ki_id": "ki_verified"},
    ]
    raw = ConsensusEngine.evaluate_cisc_consensus(
        dispute_votes, normalization="softmax", temperature=2.5
    )
    assert raw["winner"] == "ungrounded"
    assert raw.get("provenance_grounded", False) is False

    ver_map = {"ki_verified": True, "ki_unverified": False}
    grounded = ConsensusEngine.evaluate_cisc_consensus(
        dispute_votes,
        normalization="softmax",
        temperature=2.5,
        ki_verification_map=ver_map,
        provenance_multipliers=(1.0, 0.6, 0.4),
    )
    assert grounded["winner"] == "verified"
    assert grounded["provenance_grounded"] is True

    # Unverified KI (0.6x) beats ungrounded (0.4x) at equal confidence & vote count
    tie_votes = [
        {"choice": "unverified", "confidence": 0.90, "ki_id": "ki_unverified"},
        {"choice": "none", "confidence": 0.90, "ki_id": None},
    ]
    tie_res = ConsensusEngine.evaluate_cisc_consensus(
        tie_votes,
        normalization="softmax",
        temperature=2.5,
        ki_verification_map=ver_map,
    )
    assert tie_res["winner"] == "unverified"

    with pytest.raises(ValueError):
        ConsensusEngine.evaluate_cisc_consensus(
            dispute_votes,
            ki_verification_map=ver_map,
            provenance_multipliers=(1.0, -0.1, 0.4),
        )
    with pytest.raises(ValueError):
        ConsensusEngine.evaluate_cisc_consensus(
            dispute_votes,
            ki_verification_map=ver_map,
            provenance_multipliers=(1.0, 0.6),  # type: ignore[arg-type]
        )

    # Also applies provenance scaling when delegating through UncertaintyGuardService
    ctx = ServiceContext()
    await guard_plugin.on_load(ctx)
    try:
        svc_res = ConsensusEngine.evaluate_cisc_consensus(
            dispute_votes,
            normalization="softmax",
            temperature=2.5,
            uncertainty_service=guard_plugin,
            ki_verification_map=ver_map,
        )
        assert svc_res["source"] == "service.uncertainty_guard"
        assert svc_res["winner"] == "verified"
        assert svc_res["provenance_grounded"] is True
    finally:
        await guard_plugin.on_unload(ctx)

