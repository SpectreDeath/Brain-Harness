"""Failing-first contract tests for Harness Ontology-Spider vault adapter & audit fixes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from harness.services.ontology_spider import OntologySpiderKernelService
from harness.services.storage.isnad_hash import stamp_claim_sha256, verify_claim_entry
from plugins.memory_and_epistemics.ontology_spider.adapter import (
    HAS_ONTOLOGY_SPIDER,
    HarnessVaultModelSource,
)

skip_if_no_engine = pytest.mark.skipif(
    not HAS_ONTOLOGY_SPIDER,
    reason="Ontology-Spider engine is not installed",
)


@pytest.mark.unit
@skip_if_no_engine
def test_vault_adapter_unwraps_nested_isnad_claims_and_disambiguates_collisions(tmp_path: Path) -> None:
    """Nested isnad.claims[] must verify real 64-hex LF hashes, and colliding sanitized IDs stay distinct."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    vault_dir = tmp_path / ".harness" / "knowledge"
    vault_dir.mkdir(parents=True)

    for rel, body in (
        ("src/c1.py", b"CLAIM_ONE = True\n"),
        ("src/c2.py", b"CLAIM_TWO = True\n"),
        ("src/wd.py", b"WIDGET_DASH = True\n"),
        ("src/wu.py", b"WIDGET_UNDER = True\n"),
    ):
        (tmp_path / rel).write_bytes(body)

    h_c1 = stamp_claim_sha256("src/c1.py", tmp_path)
    h_c2 = stamp_claim_sha256("src/c2.py", tmp_path)
    h_wd = stamp_claim_sha256("src/wd.py", tmp_path)
    h_wu = stamp_claim_sha256("src/wu.py", tmp_path)

    ki_claims = vault_dir / "ki_nested_claims"
    ki_claims.mkdir()
    (ki_claims / "metadata.json").write_text(
        json.dumps(
            {
                "id": "ki_nested_claims",
                "title": "Nested Claims KI",
                "category": "agent_orchestration",
                "isnad": {
                    "claims": [
                        {"assertion": "Claim 1", "file": "src/c1.py", "sha256_hash": h_c1},
                        {"assertion": "Claim 2", "file": "src/c2.py", "sha256_hash": h_c2},
                    ]
                },
                "edges": [],
            }
        ),
        encoding="utf-8",
    )

    ki_unverified = vault_dir / "ki_unverified"
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
    ki_dash = vault_dir / "widget-caption"
    ki_dash.mkdir()
    (ki_dash / "metadata.json").write_text(
        json.dumps(
            {
                "id": "widget-caption",
                "title": "Widget Caption Hyphen",
                "category": "vision",
                "isnad": {
                    "claims": [{"assertion": "Dash claim", "file": "src/wd.py", "sha256_hash": h_wd}],
                },
            }
        ),
        encoding="utf-8",
    )
    ki_under = vault_dir / "widget_caption"
    ki_under.mkdir()
    (ki_under / "metadata.json").write_text(
        json.dumps(
            {
                "id": "widget_caption",
                "title": "Widget Caption Underscore",
                "category": "vision",
                "isnad": {
                    "claims": [{"assertion": "Under claim", "file": "src/wu.py", "sha256_hash": h_wu}],
                },
            }
        ),
        encoding="utf-8",
    )

    model = HarnessVaultModelSource(vault_dir).load()
    assert model.entities["ki_nested_claims"].attributes["isnad_verified"] is True
    assert model.entities["ki_nested_claims"].attributes["verified_isnad_count"] == 2
    assert model.entities["ki_unverified"].attributes["isnad_verified"] is False

    # Both widget-caption and widget_caption must survive as distinct entities
    raw_ids = {ent.attributes.get("raw_id", eid) for eid, ent in model.entities.items()}
    assert "widget-caption" in raw_ids
    assert "widget_caption" in raw_ids

    audit = OntologySpiderKernelService().audit_vault_epistemics(vault_dir)
    assert audit.status == "verified"
    assert audit.epistemic_status == "partial_unverified"
    assert audit.unverified_entities_count == 1
    assert audit.verified_entities_count == 3
    assert 0.0 < audit.isnad_verification_rate < 1.0


@pytest.mark.unit
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


@pytest.mark.unit
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


@pytest.mark.unit
@skip_if_no_engine
def test_claim_verifier_rejects_wrong_hash_and_bare_flags(tmp_path: Path) -> None:
    """Recomputing verifier must reject wrong hashes, missing local files, and bare verified/status flags."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "mod.py").write_bytes(b"def ok():\n    return 1\n")
    vault_dir = tmp_path / ".harness" / "knowledge"
    vault_dir.mkdir(parents=True)

    for ki_id, isnad_payload in (
        (
            "ki_bare_flag",
            {
                "status": "VERIFIED",
                "verified_at": "2026-11-18T00:00:00Z",
                "claims": [{"assertion": "No hash", "verified": True}],
            },
        ),
        (
            "ki_wrong_hash",
            {
                "claims": [
                    {
                        "assertion": "Wrong digest",
                        "file": "src/mod.py",
                        "sha256_hash": "0" * 64,
                        "verified": True,
                    }
                ]
            },
        ),
        (
            "ki_missing_file",
            {
                "claims": [
                    {
                        "assertion": "Missing local target",
                        "file": "src/nonexistent.py",
                        "sha256_hash": "a" * 64,
                        "verified": True,
                    }
                ]
            },
        ),
    ):
        d = vault_dir / ki_id
        d.mkdir()
        (d / "metadata.json").write_text(
            json.dumps({"id": ki_id, "title": ki_id, "category": "testing", "isnad": isnad_payload}),
            encoding="utf-8",
        )

    model = HarnessVaultModelSource(vault_dir).load()
    assert model.entities["ki_bare_flag"].attributes["isnad_verified"] is False
    assert model.entities["ki_bare_flag"].attributes["isnad_null_hash_flagged_count"] == 1
    assert model.entities["ki_wrong_hash"].attributes["isnad_verified"] is False
    assert model.entities["ki_missing_file"].attributes["isnad_verified"] is False

    assert verify_claim_entry({"verified": True}, repo_root=tmp_path).status == "MISSING_HASH_FLAGGED"
    assert (
        verify_claim_entry({"file": "src/mod.py", "sha256_hash": "0" * 64}, repo_root=tmp_path).status
        == "HASH_MISMATCH"
    )
    assert (
        verify_claim_entry({"file": "src/nonexistent.py", "sha256_hash": "a" * 64}, repo_root=tmp_path).status
        == "LOCAL_FILE_MISSING"
    )


@pytest.mark.unit
@skip_if_no_engine
def test_claim_verifier_rejects_crlf_hash_of_lf_file(tmp_path: Path) -> None:
    """Verifier must reject raw working-tree CRLF SHA-256 digests and accept canonical LF SHA-256."""
    (tmp_path / "src").mkdir()
    target = tmp_path / "src" / "win.py"
    target.write_bytes(b"def f():\r\n    return 42\r\n")

    raw_crlf_sha = hashlib.sha256(target.read_bytes()).hexdigest()
    canonical_lf_sha = stamp_claim_sha256("src/win.py", tmp_path)
    assert raw_crlf_sha != canonical_lf_sha

    vault_dir = tmp_path / ".harness" / "knowledge"
    vault_dir.mkdir(parents=True)
    for ki_id, digest in (("ki_crlf_bad", raw_crlf_sha), ("ki_lf_good", canonical_lf_sha)):
        d = vault_dir / ki_id
        d.mkdir()
        (d / "metadata.json").write_text(
            json.dumps(
                {
                    "id": ki_id,
                    "title": ki_id,
                    "category": "testing",
                    "isnad": {"claims": [{"assertion": "CRLF check", "file": "src/win.py", "sha256_hash": digest}]},
                }
            ),
            encoding="utf-8",
        )

    model = HarnessVaultModelSource(vault_dir).load()
    assert model.entities["ki_crlf_bad"].attributes["isnad_verified"] is False
    assert model.entities["ki_lf_good"].attributes["isnad_verified"] is True

