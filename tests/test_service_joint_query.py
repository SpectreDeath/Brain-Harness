"""Contract tests for cross-graph joint query service (Track 6)."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from harness.services.skill_graph.joint_query import query_knowledge_and_skills


def test_query_knowledge_and_skills_basic() -> None:
    """Execute live query against repository vault and skill graph."""
    res = query_knowledge_and_skills("reverse engineering", limit=3)
    assert res["status"] == "ok"
    assert res["topic"] == "reverse engineering"
    assert isinstance(res["knowledge_items"], list)
    assert isinstance(res["skills"], list)
    assert isinstance(res["linked_pairs"], list)
    assert "unbridged_kis" in res
    assert "ungrounded_skills" in res


def test_query_knowledge_and_skills_typed_edge_priority(tmp_path: Path) -> None:
    """Verify that became_skill typed edges take precedence over heuristic string matches."""
    vault_dir = tmp_path / "knowledge"
    vault_dir.mkdir()

    # 1. Create a synthetic KI with a typed became_skill edge
    ki_dir = vault_dir / "ki_test_sample"
    ki_dir.mkdir()
    meta = {
        "id": "ki_test_sample",
        "title": "Reverse Engineering Artifact Dissection",
        "domain": "security_and_forensics",
        "status": "ACTIVE",
        "tags": ["reverse-engineering", "dissection"],
        "isnad": {"status": "VERIFIED"},
        "edges": [
            {
                "type": "became_skill",
                "target": "rea-reverse-engineering",
                "target_kind": "skill",
            }
        ],
    }
    (ki_dir / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
    (ki_dir / "summary.md").write_text("# Summary\nSample dissection item.", encoding="utf-8")

    res = query_knowledge_and_skills(
        "reverse engineering",
        vault_dir=str(vault_dir),
        limit=5,
    )
    assert res["status"] == "ok"
    assert len(res["knowledge_items"]) == 1
    assert res["knowledge_items"][0]["ki_id"] == "ki_test_sample"
    assert res["knowledge_items"][0]["status"] == "ACTIVE"
    assert res["knowledge_items"][0]["isnad_status"] == "VERIFIED"

    # Verify that linked_pairs identifies the became_skill relationship
    matching_pairs = [
        lp for lp in res["linked_pairs"]
        if lp["ki_id"] == "ki_test_sample" and lp["skill_name"] == "rea-reverse-engineering"
    ]
    assert len(matching_pairs) == 1
    assert matching_pairs[0]["relationship"] == "became_skill"


def test_query_knowledge_and_skills_filters_demoted(tmp_path: Path) -> None:
    """Verify that DEMOTED items are filtered out by default unless include_inactive=True."""
    vault_dir = tmp_path / "knowledge"
    vault_dir.mkdir()

    # 1. Create an ACTIVE KI and a DEMOTED KI
    for ki_id, status in [("ki_active", "ACTIVE"), ("ki_demoted", "DEMOTED")]:
        d = vault_dir / ki_id
        d.mkdir()
        meta = {
            "id": ki_id,
            "title": f"Test {ki_id}",
            "status": status,
            "tags": ["test"],
        }
        (d / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        (d / "summary.md").write_text("# Summary\nTest.", encoding="utf-8")

    res_default = query_knowledge_and_skills("test", vault_dir=str(vault_dir))
    assert len(res_default["knowledge_items"]) == 1
    assert res_default["knowledge_items"][0]["ki_id"] == "ki_active"

    res_inactive = query_knowledge_and_skills("test", vault_dir=str(vault_dir), include_inactive=True)
    assert len(res_inactive["knowledge_items"]) == 2

