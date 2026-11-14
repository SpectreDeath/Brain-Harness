"""Top-level contract tests for the TrustGraph Ontology Governor micro-kernel service."""

from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess
import sys

import pytest

from harness.creator.skills import SkillValidator
from harness.services import (
    EXPLAINABILITY_STAGES,
    LAYA_HEAD_MAX_LEN,
    LAYA_MAX_SEQ_LEN,
    LAYA_QUESTION_TYPES,
    LAYA_TEMP_MAX,
    LAYA_TEMP_MIN,
    POLICY_GRAPH_URI,
    RETRIEVAL_GRAPH_URI,
    SOURCE_GRAPH_URI,
    TRUSTGRAPH_GOVERNOR_KEY,
    LayaDecisionScoreReport,
    OntologyValidationReport,
    ProvenanceTraceEnvelope,
    ShaclPolicyFilterReport,
    TrustGraphGovernorEngine,
    TrustGraphGovernorProtocol,
)
from harness.services._domains._memory_and_epistemics import (
    TRUSTGRAPH_GOVERNOR_KEY as DOMAIN_TRUSTGRAPH_KEY,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "trustgraph-ontology-governor"
SKILL_CLI = SKILL_DIR / "scripts" / "trustgraph_governor_engine.py"


def test_service_exports_protocol_and_slotted_frozen_dataclasses() -> None:
    assert TRUSTGRAPH_GOVERNOR_KEY is DOMAIN_TRUSTGRAPH_KEY
    engine = TrustGraphGovernorEngine()
    assert isinstance(engine, TrustGraphGovernorProtocol)

    report = engine.evaluate_shacl_policy_filter(triples=[], policies=[])
    assert isinstance(report, ShaclPolicyFilterReport)
    assert hasattr(report, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        report.open_mode = False  # type: ignore[misc]


def test_shacl_policy_filter_order_first_match_and_open_mode() -> None:
    engine = TrustGraphGovernorEngine()
    triples = [
        {"s": "urn:doc:secret", "p": "ex:title", "o": "Top Secret"},
        {"s": "urn:doc:override-allow", "p": "ex:title", "o": "Cleared"},
        {"s": "urn:doc:public", "p": "ex:title", "o": "Public"},
    ]

    # Empty policies -> explicit open mode
    open_rep = engine.evaluate_shacl_policy_filter(triples=triples, policies=[])
    assert open_rep.open_mode is True
    assert len(open_rep.allowed_triples) == 3
    assert len(open_rep.dropped_triples) == 0
    assert open_rep.cache_limits["query_cache_ttl_s"] == 30
    assert open_rep.cache_limits["node_cache_max"] == 1024

    # High-priority sh:order=1 allow rule wins before default sh:order=99 blocks=True rule
    policies = [
        {
            "shape_uri": f"{POLICY_GRAPH_URI}#block-classified",
            # order omitted -> defaults to 99; blocks omitted -> defaults to True
            "predicate": "classification",
            "equals": "secret",
        },
        {
            "shape_uri": f"{POLICY_GRAPH_URI}#allow-override",
            "order": 1,
            "blocks": False,
            "target_class": "ClearedDoc",
            "predicate": "classification",
            "equals": "secret",
        },
    ]
    attrs = {
        "urn:doc:secret": {"type": "InternalDoc", "classification": "secret"},
        "urn:doc:override-allow": {"type": "ClearedDoc", "classification": "secret"},
        "urn:doc:public": {"type": "PublicDoc", "classification": "public"},
    }

    rep = engine.evaluate_shacl_policy_filter(triples=triples, policies=policies, subject_attributes=attrs)
    assert rep.open_mode is False
    assert rep.evaluated_policies == (
        f"{POLICY_GRAPH_URI}#allow-override",
        f"{POLICY_GRAPH_URI}#block-classified",
    )
    assert rep.blocked_subjects == ("urn:doc:secret",)
    assert len(rep.dropped_triples) == 1
    assert rep.dropped_triples[0]["s"] == "urn:doc:secret"
    assert [t["s"] for t in rep.allowed_triples] == ["urn:doc:override-allow", "urn:doc:public"]


def test_ontology_validation_bypass_subclass_closure_and_cycle_guard() -> None:
    engine = TrustGraphGovernorEngine()
    # Small ontology: 2 classes + 1 object_prop + 1 datatype_prop = 4 < 5 -> bypasses selector
    small_onto = {
        "classes": {
            "Agent": {},
            "Person": {"subClassOf": ["Agent"]},
        },
        "object_properties": {
            "authored": {"domain": "Agent", "range": "Document"},
        },
        "datatype_properties": {
            "age": {"domain": "Agent"},
        },
    }
    small_onto["classes"]["Document"] = {}  # total = 3 + 1 + 1 = 5 -> check boundary (< 5 vs >= 5)
    # Use 4 elements first to test bypass=True
    compact = {
        "classes": {"Agent": {}, "Person": {"subClassOf": ["Agent"]}},
        "object_properties": {"worksFor": {"domain": "Agent", "range": "Agent"}},
        "datatype_properties": {"name": {"domain": "Agent"}},
    }
    triples = [
        {
            "kind": "relationship",
            "s": "ex:alice",
            "predicate": "worksFor",
            "o": "ex:org1",
            "subject_type": "Person",  # subClassOf Agent -> valid domain!
            "object_type": "Agent",
        },
        {
            "kind": "attribute",
            "s": "ex:alice",
            "predicate": "name",
            "value": "Alice",
            "entity_type": "Person",  # subClassOf Agent -> valid domain!
        },
        {
            "kind": "relationship",
            "s": "ex:alice",
            "predicate": "worksFor",
            "o": "ex:stone",
            "subject_type": "Person",
            "object_type": "Inanimate",  # invalid range!
        },
    ]
    rep = engine.validate_ontology_extractions(ontology=compact, triples=triples, bypass_selector_below=5)
    assert isinstance(rep, OntologyValidationReport)
    assert rep.total_elements == 4
    assert rep.selector_bypassed is True
    assert len(rep.accepted_triples) == 2
    assert len(rep.rejected_triples) == 1
    assert "range_mismatch" in rep.rejected_triples[0]["reason"]

    # Cyclic ontology + >= 5 elements -> terminates cleanly, selector not bypassed
    cyclic_onto = {
        "classes": {
            "A": {"subClassOf": ["B"]},
            "B": {"subClassOf": ["A"]},
            "C": {},
        },
        "object_properties": {"rel": {"domain": "A", "range": "C"}},
        "datatype_properties": {"score": {"domain": "B"}},
    }
    cyclic_rep = engine.validate_ontology_extractions(
        ontology=cyclic_onto,
        triples=[
            {"kind": "relationship", "s": "x", "predicate": "rel", "o": "y", "subject_type": "B", "object_type": "C"}
        ],
    )
    assert cyclic_rep.selector_bypassed is False
    assert cyclic_rep.total_elements == 5
    assert cyclic_rep.cycles_detected  # cycles recorded without infinite recursion
    assert len(cyclic_rep.accepted_triples) == 1  # B is a subclass of A via A<->B cycle

    with pytest.raises((AttributeError, TypeError)):
        cyclic_rep.total_elements = 999  # type: ignore[misc]


def test_provenance_dual_named_graphs_and_token_triples() -> None:
    engine = TrustGraphGovernorEngine()
    env = engine.build_provenance_trace(
        question_id="req-007",
        query_text="Explain SHACL policy filters",
        document_id="trustgraph-spec-v1",
        extraction_triples=[{"s": "https://trustgraph.ai/entity/shacl", "p": "rdf:type", "o": "Standard"}],
        stage_details={"grounding": "Matched urn:graph:policy", "synthesis": "Summarized 2 rules"},
        prompt_tokens=200,
        completion_tokens=80,
    )
    assert isinstance(env, ProvenanceTraceEnvelope)
    assert env.source_graph == SOURCE_GRAPH_URI
    assert env.retrieval_graph == RETRIEVAL_GRAPH_URI
    assert env.question_uri == "urn:trustgraph:question:req-007"
    assert tuple(env.stage_uris.keys()) == EXPLAINABILITY_STAGES
    assert all(t["g"] == SOURCE_GRAPH_URI for t in env.extraction_triples)
    assert any(t["s"].startswith("https://trustgraph.ai/doc/") for t in env.extraction_triples)
    assert all(t["g"] == RETRIEVAL_GRAPH_URI for t in env.explainability_triples)
    assert any("token/total" in t["p"] and t["o"] == "280" for t in env.explainability_triples)
    assert env.token_triples_appended is True
    assert env.total_tokens == 280


def test_laya_decision_scoring_temperature_entropy_and_budget() -> None:
    engine = TrustGraphGovernorEngine()
    assert LAYA_QUESTION_TYPES == {"choice": 0, "score": 1, "noul": 2}

    # NaN temperature -> clamped safely to 1.0
    nan_rep = engine.score_laya_decision(
        question_type="choice",
        options=["opt0", "opt1", "opt2"],
        logits_or_probs=[3.0, 1.0, 0.0],
        temperature=float("nan"),
        option_tokens_each=10,
    )
    assert isinstance(nan_rep, LayaDecisionScoreReport)
    assert nan_rep.clamped_temperature == 1.0
    assert nan_rep.selected_index == 0
    assert 0.0 <= nan_rep.confidence <= 1.0
    assert math.isclose(sum(nan_rep.probabilities), 1.0, rel_tol=1e-4)

    # Temperature extremes clamp to [0.5, 5.0]
    cold_rep = engine.score_laya_decision("score", ["a", "b"], [1.0, 1.0], temperature=0.05)
    hot_rep = engine.score_laya_decision("noul", ["a", "b"], [1.0, 1.0], temperature=99.0)
    assert cold_rep.clamped_temperature == LAYA_TEMP_MIN
    assert hot_rep.clamped_temperature == LAYA_TEMP_MAX
    assert math.isclose(cold_rep.confidence, 0.0, abs_tol=1e-5)  # uniform k=2 -> 0 confidence

    # k < 2 -> confidence == 1.0 without ln(1) division by zero
    single_rep = engine.score_laya_decision("choice", ["only"], [1.0])
    assert single_rep.confidence == 1.0
    assert single_rep.entropy == 0.0

    # opt_budget < 16 triggers shrink_warning=True
    dense_rep = engine.score_laya_decision(
        question_type="choice",
        options=[f"o{i}" for i in range(6)],
        logits_or_probs=[1.0] * 6,
        option_tokens_each=35,  # 192 - 6*(1 + 35) = -24 < 16
    )
    assert dense_rep.head_max_len == LAYA_HEAD_MAX_LEN
    assert dense_rep.max_seq_len == LAYA_MAX_SEQ_LEN
    assert dense_rep.opt_budget < 16
    assert dense_rep.shrink_warning is True


@pytest.mark.asyncio
async def test_skill_validator_and_cli_subprocess_execution() -> None:
    report = await SkillValidator.validate_async(SKILL_DIR)
    assert report.valid, f"Skill validation checks failed: {report.errors}"

    proc = subprocess.run(
        [
            sys.executable,
            str(SKILL_CLI),
            "filter-policy",
            "--triples-json",
            json.dumps([{"s": "urn:s1", "p": "ex:p", "o": "val"}]),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["open_mode"] is True
    assert len(payload["allowed_triples"]) == 1
