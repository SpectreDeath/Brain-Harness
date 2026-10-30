"""Unit and CLI contract tests for knowledge vault hygiene and triaging."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.commands.reflection import knowledge_group
from harness.services.storage.models import KnowledgeItemRecord
from harness.services.storage.vault_hygiene import (
    audit_vault_hygiene,
    suggest_category_for_item,
    suggest_tags_for_item,
)
from harness.services.storage.vault_taxonomy import TaxonomyDomain


def test_suggest_category_retains_existing() -> None:
    ki = KnowledgeItemRecord(
        id="ki-test-1",
        title="Test item",
        category="security_and_forensics",
        tags=["security", "sandbox"],
    )
    cat = suggest_category_for_item(ki)
    assert cat == "security_and_forensics"


def test_suggest_category_maps_uncategorized() -> None:
    ki_agent = KnowledgeItemRecord(
        id="ki-test-agent",
        title="Agent Swarm Orchestration with Subagents",
        category="general",
        tags=["worker", "swarm"],
    )
    assert suggest_category_for_item(ki_agent) == TaxonomyDomain.AGENT_ORCHESTRATION.value

    ki_sec = KnowledgeItemRecord(
        id="ki-test-sec",
        title="Subprocess Sandboxing and Vulnerability Auditing",
        category="",
        tags=["sandbox"],
    )
    assert suggest_category_for_item(ki_sec) == TaxonomyDomain.SECURITY_AND_FORENSICS.value


def test_suggest_tags_for_known_and_unknown() -> None:
    ki_known = KnowledgeItemRecord(
        id="ki-5d-complexity-baseline",
        title="5D Complexity Scoring Baseline",
        category="general",
        tags=[],
    )
    tags_known = suggest_tags_for_item(ki_known)
    assert "complexity_scoring" in tags_known
    assert "architecture" in tags_known

    ki_unknown = KnowledgeItemRecord(
        id="ki-custom-topic",
        title="Kubernetes Ingress Controller Tuning",
        category="general",
        tags=[],
    )
    tags_unknown = suggest_tags_for_item(ki_unknown)
    assert len(tags_unknown) > 0
    assert "kubernetes" in tags_unknown


def test_audit_vault_hygiene_metrics() -> None:
    items = [
        KnowledgeItemRecord(id="k1", title="One", category="general", tags=[]),
        KnowledgeItemRecord(id="k2", title="Two", category="developer_experience", tags=["python"]),
    ]
    audit = audit_vault_hygiene(items)
    assert audit["uncategorized_count"] == 1
    assert audit["untagged_count"] == 1
    assert audit["uncategorized"][0]["id"] == "k1"
    assert audit["untagged"][0]["id"] == "k1"


def test_cli_knowledge_hygiene_dry_run_and_apply(tmp_path: Path) -> None:
    vault_dir = tmp_path / "knowledge"
    vault_dir.mkdir(parents=True)

    ki_dir = vault_dir / "ki-test-hygiene"
    ki_dir.mkdir()
    meta = {
        "id": "ki-test-hygiene",
        "title": "Cli Monolith Decomposition Refactoring",
        "category": "general",
        "tags": [],
        "extra_custom_key": "preserved_value",
    }
    (ki_dir / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
    (ki_dir / "summary.md").write_text("# Summary\nDecomposition notes.", encoding="utf-8")

    runner = CliRunner()

    # Dry run
    res = runner.invoke(knowledge_group, ["hygiene", "--vault", str(vault_dir)])
    assert res.exit_code == 0
    assert "Uncategorized Items:     1" in res.output
    assert "Untagged Items:          1" in res.output

    # Check that disk was NOT modified in dry run
    raw_before = json.loads((ki_dir / "metadata.json").read_text(encoding="utf-8"))
    assert raw_before["category"] == "general"
    assert raw_before["tags"] == []
    assert raw_before["extra_custom_key"] == "preserved_value"

    # Apply changes
    res_apply = runner.invoke(knowledge_group, ["hygiene", "--vault", str(vault_dir), "--apply"])
    assert res_apply.exit_code == 0
    assert "Successfully applied hygiene updates" in res_apply.output

    # Check that disk WAS modified and extra keys preserved
    raw_after = json.loads((ki_dir / "metadata.json").read_text(encoding="utf-8"))
    assert raw_after["category"] != "general"
    assert len(raw_after["tags"]) > 0
    assert raw_after["extra_custom_key"] == "preserved_value"

    # Re-run hygiene — should now report 0 uncategorized and 0 untagged
    res_clean = runner.invoke(knowledge_group, ["hygiene", "--vault", str(vault_dir), "--json"])
    assert res_clean.exit_code == 0
    data = json.loads(res_clean.output)
    assert data["audit"]["uncategorized_count"] == 0
    assert data["audit"]["untagged_count"] == 0

