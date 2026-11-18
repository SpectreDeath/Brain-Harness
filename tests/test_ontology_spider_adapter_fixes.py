"""Failing-first contract tests for Harness Ontology-Spider vault adapter & audit fixes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.services.ontology_spider import OntologySpiderKernelService
from plugins.memory_and_epistemics.ontology_spider.adapter import (
    HAS_ONTOLOGY_SPIDER,
    HarnessVaultModelSource,
)

skip_if_no_engine = pytest.mark.skipif(
    not HAS_ONTOLOGY_SPIDER,
    reason="Ontology-Spider engine is not installed",
)


@skip_if_no_engine
def test_vault_adapter_unwraps_nested_isnad_claims_and_disambiguates_collisions(tmp_path: Path) -> None:
    """Nested isnad.claims[] verified flags must count as verified, and colliding sanitized IDs stay distinct."""
    ki_claims = tmp_path / "ki_nested_claims"
    ki_claims.mkdir()
    (ki_claims / "metadata.json").write_text(
        json.dumps(
            {
                "id": "ki_nested_claims",
                "title": "Nested Claims KI",
                "category": "agent_orchestration",
                "isnad": {
                    "claims": [
                        {"assertion": "Claim 1", "verified": True},
                        {"assertion": "Claim 2", "verified": True},
                    ]
                },
                "edges": [],
            }
        ),
        encoding="utf-8",
    )

    ki_unverified = tmp_path / "ki_unverified"
    ki_unverified.mkdir()
    (ki_unverified / "metadata.json").write_text(
        json.dumps(
            {
                "id": "ki_unverified",
                "title": "Unverified KI",
                "category": "agent_orchestration",
                "isnad": {"claims": [{"assertion": "Unchecked", "verified": False}]},
                "edges": [],
            }
        ),
        encoding="utf-8",
    )

    # Collision pair: widget-caption vs widget_caption
    ki_dash = tmp_path / "widget-caption"
    ki_dash.mkdir()
    (ki_dash / "metadata.json").write_text(
        json.dumps(
            {
                "id": "widget-caption",
                "title": "Widget Caption Hyphen",
                "category": "vision",
                "isnad": {"status": "VERIFIED"},
            }
        ),
        encoding="utf-8",
    )
    ki_under = tmp_path / "widget_caption"
    ki_under.mkdir()
    (ki_under / "metadata.json").write_text(
        json.dumps(
            {
                "id": "widget_caption",
                "title": "Widget Caption Underscore",
                "category": "vision",
                "isnad": {"status": "VERIFIED"},
            }
        ),
        encoding="utf-8",
    )

    model = HarnessVaultModelSource(tmp_path).load()
    assert model.entities["ki_nested_claims"].attributes["isnad_verified"] is True
    assert model.entities["ki_nested_claims"].attributes["verified_isnad_count"] == 2
    assert model.entities["ki_unverified"].attributes["isnad_verified"] is False

    # Both widget-caption and widget_caption must survive as distinct entities
    raw_ids = {ent.attributes.get("raw_id", eid) for eid, ent in model.entities.items()}
    assert "widget-caption" in raw_ids
    assert "widget_caption" in raw_ids

    audit = OntologySpiderKernelService().audit_vault_epistemics(tmp_path)
    assert audit.status == "verified"
    assert audit.epistemic_status == "partial_unverified"
    assert audit.unverified_entities_count == 1
    assert audit.verified_entities_count == 3
    assert 0.0 < audit.isnad_verification_rate < 1.0


@skip_if_no_engine
def test_code_edge_normalizes_src_module_paths(tmp_path: Path) -> None:
    """Path-style src/ module targets on applicable_to/references_code also emit canonical references_code."""
    ki_dir = tmp_path / "ki_path_edges"
    ki_dir.mkdir()
    (ki_dir / "metadata.json").write_text(
        json.dumps(
            {
                "id": "ki_path_edges",
                "title": "Path Edge Normalization Test",
                "category": "agent_orchestration",
                "isnad": {"status": "VERIFIED"},
                "edges": [
                    {
                        "type": "applicable_to",
                        "target": "src/harness/services/uncertainty_guard.py",
                        "target_kind": "module",
                        "confidence": 0.85,
                    },
                    {
                        "type": "references_code",
                        "target": "src/harness/services/deep_auditor/__init__.py",
                        "target_kind": "module",
                        "confidence": 1.0,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    model = HarnessVaultModelSource(tmp_path).load()
    triples = {(a.relation.subject, a.relation.predicate, a.relation.object) for a in model.assertions.values()}

    assert ("ki_path_edges", "references_code", "harness_services_uncertainty_guard") in triples
    assert ("ki_path_edges", "references_code", "harness_services_deep_auditor") in triples
    # Original raw edges are preserved
    assert ("ki_path_edges", "applicable_to", "src_harness_services_uncertainty_guard_py") in triples
    assert ("ki_path_edges", "references_code", "src_harness_services_deep_auditor___init___py") in triples


@skip_if_no_engine
def test_code_edge_strips_pre_sanitized_src_and_py_suffix(tmp_path: Path) -> None:
    """Pre-sanitized src_*_py targets and dotted applicable_to module targets normalize cleanly without dupes."""
    ki_dir = tmp_path / "ki_sanitized_edges"
    ki_dir.mkdir()
    (ki_dir / "metadata.json").write_text(
        json.dumps(
            {
                "id": "ki_sanitized_edges",
                "title": "Pre-Sanitized Edge Normalization Test",
                "category": "agent_orchestration",
                "isnad": {"status": "VERIFIED"},
                "edges": [
                    {"type": "references_code", "target": "src_harness_services_uncertainty_guard_py"},
                    {"type": "references_code", "target": "src/harness/services/uncertainty_guard.py"},
                    {"type": "references_code", "target": "src_harness_services_deep_auditor___init___py"},
                    {
                        "type": "applicable_to",
                        "target": "harness.services.vector_index",
                        "target_kind": "module",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    model = HarnessVaultModelSource(tmp_path).load()
    triples = [(a.relation.subject, a.relation.predicate, a.relation.object) for a in model.assertions.values()]
    triple_set = set(triples)

    assert ("ki_sanitized_edges", "references_code", "harness_services_uncertainty_guard") in triple_set
    assert ("ki_sanitized_edges", "references_code", "harness_services_deep_auditor") in triple_set
    assert ("ki_sanitized_edges", "references_code", "harness_services_vector_index") in triple_set
    assert (
        triples.count(("ki_sanitized_edges", "references_code", "harness_services_uncertainty_guard")) == 1
    )

