"""Top-level mirror contract tests for Graphiti / Zep Temporal Memory Governor."""

from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess
import sys

import pytest

from harness.creator.skills import SkillValidator
from harness.services import (
    CENTER_NODE_SELF_DISTANCE,
    DEFAULT_MMR_LAMBDA,
    DEFAULT_MMR_MIN_SCORE,
    DEFAULT_RRF_RANK_CONST,
    ENTITY_BASE_LABEL,
    FUZZY_JACCARD_THRESHOLD,
    GRAPHITI_ZEP_MEMORY_KEY,
    MIN_NAME_LENGTH,
    MIN_TOKEN_COUNT,
    MINHASH_BAND_SIZE,
    MINHASH_PERMUTATIONS,
    NAME_ENTROPY_THRESHOLD,
    SUPPORTED_RERANK_METHODS,
    ZEP_WIRE_PROPERTY_TYPES,
    BiTemporalEdgeNormalizationReport,
    CommunityAndOntologyReport,
    EntityDedupResolutionReport,
    GraphitiZepMemoryEngine,
    GraphitiZepMemoryProtocol,
    HybridRerankReport,
)
from harness.services._domains._memory_and_epistemics import (
    GRAPHITI_ZEP_MEMORY_KEY as DOMAIN_ZEP_KEY,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "graphiti-zep-memory-governor"
SKILL_CLI = SKILL_DIR / "scripts" / "graphiti_zep_memory_engine.py"


def test_exports_protocol_and_slotted_frozen_dataclasses() -> None:
    assert GRAPHITI_ZEP_MEMORY_KEY is DOMAIN_ZEP_KEY
    assert NAME_ENTROPY_THRESHOLD == 1.5
    assert MIN_NAME_LENGTH == 6
    assert MIN_TOKEN_COUNT == 2
    assert FUZZY_JACCARD_THRESHOLD == 0.9
    assert MINHASH_PERMUTATIONS == 32
    assert MINHASH_BAND_SIZE == 4
    assert ENTITY_BASE_LABEL == "Entity"
    assert DEFAULT_RRF_RANK_CONST == 1
    assert DEFAULT_MMR_LAMBDA == 0.5
    assert DEFAULT_MMR_MIN_SCORE == -2.0
    assert CENTER_NODE_SELF_DISTANCE == 0.1
    assert ZEP_WIRE_PROPERTY_TYPES == ("text", "int", "float", "boolean")
    assert SUPPORTED_RERANK_METHODS == ("rrf", "mmr", "node_distance")

    engine = GraphitiZepMemoryEngine()
    assert isinstance(engine, GraphitiZepMemoryProtocol)

    rep = engine.normalize_bitemporal_edges("Alice works at Acme", "2026-11-10T00:00:00Z")
    assert isinstance(rep, BiTemporalEdgeNormalizationReport)
    assert hasattr(rep, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        rep.fact = "mutated"  # type: ignore[misc]


def test_bitemporal_future_clamping_deadlines_and_contradictions() -> None:
    engine = GraphitiZepMemoryEngine()

    # Future assertion + soft deadline ("by") without ongoing state end -> clamp valid_at & clear invalid_at
    rep_soft = engine.normalize_bitemporal_edges(
        fact="Bob is scheduled to complete the migration due by Friday",
        reference_time="2026-11-01T10:00:00Z",
        valid_at="2026-11-08T00:00:00Z",
        invalid_at="2026-11-09T00:00:00Z",
        existing_edges=[{"uuid": "edge-old-1"}, {"uuid": "edge-keep-2"}],
        contradicted_ids=["edge-old-1"],
    )
    assert rep_soft.future_assertion_detected is True
    assert rep_soft.soft_deadline_cleared is True
    assert rep_soft.normalized_valid_at == "2026-11-01T10:00:00+00:00"
    assert rep_soft.normalized_invalid_at is None
    assert rep_soft.contradicted_edge_ids == ("edge-old-1",)
    assert rep_soft.surviving_edge_ids == ("edge-keep-2",)

    # Ongoing state end ("until") preserves invalid_at even when future assertion present
    rep_end = engine.normalize_bitemporal_edges(
        fact="Service will remain available until next month",
        reference_time="2026-11-01T10:00:00Z",
        valid_at="2026-11-05T00:00:00Z",
        invalid_at="2026-12-01T00:00:00Z",
    )
    assert rep_end.future_assertion_detected is True
    assert rep_end.soft_deadline_cleared is False
    assert rep_end.normalized_valid_at == "2026-11-01T10:00:00+00:00"
    assert rep_end.normalized_invalid_at == "2026-12-01T00:00:00+00:00"


def test_entropy_gated_minhash_lsh_and_dangling_endpoint_pruning() -> None:
    engine = GraphitiZepMemoryEngine()
    existing = [
        {
            "uuid": "ent-1",
            "name": "OpenTelemetry Distributed Tracing Collector Pipeline",
            "labels": ["Entity", "Service"],
        },
        {
            "uuid": "ent-2",
            "name": "Acme Corp",
            "labels": ["Entity", "Organization"],
        },
    ]
    extracted = [
        # Near-identical long high-entropy name differing only slightly -> MinHash/LSH Jaccard >= 0.9 match + label promotion
        {
            "uuid": "ext-1",
            "name": "OpenTelemetry Distributed Tracing Collector Pipelines",
            "labels": ["Entity", "Service", "TelemetryNode"],
        },
        # Exact normalized match (extra whitespace + case diff)
        {
            "uuid": "ext-2",
            "name": "  acme   corp ",
            "labels": ["Organization"],
        },
        # Low-entropy short/repetitive string -> deferred to LLM
        {
            "uuid": "ext-3",
            "name": "AAA",
            "labels": ["Entity"],
        },
    ]
    rep = engine.resolve_entities_and_endpoints(
        extracted_entities=extracted,
        existing_entities=existing,
        edge_endpoints=[
            ("Acme Corp", "v1.4.2-release"),
            ("Acme Corp", "dropped-endpoint"),
        ],
        kept_edge_endpoints=[("Acme Corp", "v1.4.2-release")],
    )
    assert isinstance(rep, EntityDedupResolutionReport)
    assert (
        "OpenTelemetry Distributed Tracing Collector Pipelines",
        "OpenTelemetry Distributed Tracing Collector Pipeline",
    ) in rep.duplicate_pairs
    assert ("  acme   corp ", "Acme Corp") in rep.duplicate_pairs
    assert rep.resolved_entities[0]["labels"] == ["Entity", "Service", "TelemetryNode"]
    assert rep.llm_deferred_names == ("AAA",)
    assert set(rep.materialized_endpoints) == {"v1.4.2-release", "dropped-endpoint"}
    assert rep.pruned_endpoints == ("dropped-endpoint",)

    with pytest.raises((AttributeError, TypeError)):
        rep.llm_deferred_names = ()  # type: ignore[misc]


def test_hybrid_reranking_rrf_mmr_and_node_distance() -> None:
    engine = GraphitiZepMemoryEngine()

    # RRF: node-b appears 1st in list 2 and 2nd in list 1 -> highest reciprocal score (1/(0+1) + 1/(1+1) = 1.5)
    rrf_rep = engine.rerank_hybrid_results(
        method="rrf",
        ranked_lists=[["node-a", "node-b"], ["node-b", "node-c"]],
        min_score=0.6,
    )
    assert isinstance(rrf_rep, HybridRerankReport)
    assert rrf_rep.ranked_uuids[0] == "node-b"
    assert math.isclose(rrf_rep.scores[0], 1.5, rel_tol=1e-5)
    assert rrf_rep.filtered_count == 1  # node-c has 0.5 < 0.6

    # MMR: L2-normalized diversity scoring
    mmr_rep = engine.rerank_hybrid_results(
        method="mmr",
        query_vector=[1.0, 0.0],
        candidate_vectors={
            "v1": [10.0, 0.0],  # aligned with query, same as v2
            "v2": [1.0, 0.0],
            "v3": [0.0, 5.0],  # orthogonal to query & others -> lower redundancy penalty
        },
        mmr_lambda=0.5,
        min_score=-2.0,
    )
    assert len(mmr_rep.ranked_uuids) == 3
    assert set(mmr_rep.ranked_uuids) == {"v1", "v2", "v3"}

    # node_distance: center_node self-distance 0.1 -> score 10.0
    dist_rep = engine.rerank_hybrid_results(
        method="node_distance",
        center_node_uuid="center",
        hop_distances={"center": 99.0, "near": 1.0, "far": 2.0, "unlinked": math.inf},
        min_score=0.1,
    )
    assert dist_rep.ranked_uuids == ("center", "near", "far")
    assert dist_rep.scores[0] == 10.0
    assert dist_rep.filtered_count == 1  # unlinked has score 0.0 < 0.1


def test_community_clustering_group_queues_and_typed_ontology_compilation() -> None:
    engine = GraphitiZepMemoryEngine()
    projection = {
        "n1": [{"node_uuid": "n2", "edge_count": 2}, {"node_uuid": "n3", "edge_count": 2}],
        "n2": [{"node_uuid": "n1", "edge_count": 2}, {"node_uuid": "n3", "edge_count": 2}],
        "n3": [{"node_uuid": "n1", "edge_count": 2}, {"node_uuid": "n2", "edge_count": 2}],
        "iso": [],
    }
    valid_entities = [
        {
            "name": "Traveler",
            "description": "Someone who takes trips.",
            "fields": [
                {"name": "home_city", "type": "text", "description": "City they live in", "identity": True},
                {"name": "internal_scratch", "type": "text", "description": "Ignored", "excluded": True},
            ],
        }
    ]
    valid_edges = [
        {
            "name": "TRAVELED_TO",
            "description": "A traveler visiting a destination.",
            "fields": [{"name": "nights", "type": "int", "description": "Number of nights"}],
            "source_targets": [{"source": "Traveler", "target": "Destination"}],
        }
    ]
    rep = engine.cluster_communities_and_compile_ontology(
        neighbor_projection=projection,
        episode_batches=[{"group_id": "g1"}, {"group_id": "g1"}, {"group_id": "g2"}],
        entity_schemas=valid_entities,
        edge_schemas=valid_edges,
    )
    assert isinstance(rep, CommunityAndOntologyReport)
    assert rep.sequential_groups_verified is True
    assert rep.group_queue_depths == {"g1": 2, "g2": 1}
    assert rep.ontology_valid is True
    assert any(set(c) == {"n1", "n2", "n3"} for c in rep.communities)
    assert ("iso",) in rep.communities
    assert rep.compiled_entity_types[0]["identity_properties"] == ["home_city"]
    assert len(rep.compiled_entity_types[0]["properties"]) == 1  # excluded field omitted

    # Invalid ontology: edge field marked Identity + empty entity docstring
    bad_rep = engine.cluster_communities_and_compile_ontology(
        neighbor_projection={"x": []},
        entity_schemas=[{"name": "NoDoc", "description": "", "fields": []}],
        edge_schemas=[
            {
                "name": "BAD_EDGE",
                "description": "Has forbidden identity",
                "fields": [{"name": "k", "type": "text", "description": "bad", "identity": True}],
            }
        ],
    )
    assert bad_rep.ontology_valid is False
    assert any("entity_missing_description:NoDoc" in v for v in bad_rep.violations)
    assert any("edge_identity_forbidden:BAD_EDGE.k" in v for v in bad_rep.violations)


@pytest.mark.asyncio
async def test_skill_validator_and_cli_subprocess_execution() -> None:
    report = await SkillValidator.validate_async(SKILL_DIR)
    assert report.valid, f"Skill validation checks failed: {report.errors}"

    proc = subprocess.run(
        [
            sys.executable,
            str(SKILL_CLI),
            "rerank-hybrid",
            "--method",
            "rrf",
            "--ranked-lists-json",
            json.dumps([["a", "b"], ["b", "c"]]),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ranked_uuids"][0] == "b"
