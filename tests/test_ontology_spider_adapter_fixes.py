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
