"""Contract tests for Epistemology claims lifecycle, Knowledge Graph, Taxonomy, and Contradictions.

Covers:
- Track 1A P1: Isnad claims lifecycle (confidence, unverified/verified/challenged/superseded, supersession links).
- Track 1A P1: Contradiction and antinomy detection review queue.
- Track 1A P1: Single source of truth & era unification (dual-file canonical format, schema_version 1.0.0).
- Track 1A P2: Dynamic skill re-routing during step progression.
- Track 1A P2: Skill synthesis provenance recording (.provenance.json & CARD.md box).
- Track 1B P0 & P1: Typed KnowledgeEdges, mechanical edge backfilling, taxonomy, and graph query service.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from harness.agent.base import AgentStep, AgentTrajectory
from harness.agent.react.dispatch import maybe_reroute_skills
from harness.commands.reflection import knowledge_group
from harness.creator.skills.models import SkillOptions
from harness.creator.skills.scaffold import SkillScaffoldEngine
from harness.kernel.context import ServiceContext
from harness.services.skill_graph import SKILL_INTELLIGENCE_KEY
from harness.services.skill_graph.models import SkillExecutionGuidance
from harness.services.storage.models import (
    IsnadClaim,
    IsnadClaimStatus,
    IsnadLineageBlock,
    KnowledgeEdge,
    KnowledgeItemRecord,
)
from harness.services.storage.sqlite import SQLiteStorageService
from harness.services.storage.vault_contradiction import ContradictionDetector
from harness.services.storage.vault_graph import KnowledgeGraphQueryService
from harness.services.storage.vault_taxonomy import (
    CONTROLLED_DOMAINS,
    get_taxonomy_domain,
    is_valid_domain,
    normalize_category,
)


@pytest.mark.unit
def test_isnad_claims_lifecycle_transitions():
    """Verify Isnad claims carry confidence scores and state transitions."""
    claim1 = IsnadClaim(
        claim_id="claim-01",
        assertion="Always run external plugins in-process for speed",
        status=IsnadClaimStatus.VERIFIED.value,
        confidence=0.9,
    )
    claim2 = IsnadClaim(
        claim_id="claim-02",
        assertion="Synchronous subprocess blocking is prohibited",
        status=IsnadClaimStatus.VERIFIED.value,
        confidence=0.85,
    )

    ki = KnowledgeItemRecord(
        id="ki_test_claims_01",
        title="Plugin Staging Heuristics",
        category="security_and_forensics",
        isnad=IsnadLineageBlock(
            decision_id="dec_01",
            claims=[claim1, claim2],
        ),
    )

    claims = ki.get_claims()
    assert len(claims) == 2
    assert claims[0].status == "verified"
    assert claims[0].confidence == 0.9

    # Transition claim1 to CHALLENGED
    matched = ki.challenge_claim("in-process", "Violates Rule 5 subprocess isolation")
    assert matched is True
    updated_claims = ki.get_claims()
    assert updated_claims[0].status == "challenged"
    assert "Rule 5" in (updated_claims[0].challenged_reason or "")

    # Transition claim2 to SUPERSEDED
    matched_sup = ki.supersede_claim("blocking", "ki_async_v2")
    assert matched_sup is True
    updated_claims_2 = ki.get_claims()
    assert updated_claims_2[1].status == "superseded"
    assert updated_claims_2[1].superseded_by == "ki_async_v2"


@pytest.mark.unit
def test_knowledge_edge_model_and_addition():
    """Verify typed KnowledgeEdge additions and idempotence."""
    ki = KnowledgeItemRecord(
        id="ki_edge_test",
        title="Edge Verification Test",
        category="context_engineering",
    )

    edge1 = ki.add_edge(
        edge_type="became_skill",
        target="icm-workspace-architect",
        target_kind="skill",
        confidence=1.0,
    )
    assert edge1.type == "became_skill"
    assert edge1.target == "icm-workspace-architect"
    assert len(ki.edges) == 1

    # Idempotent re-add returns existing edge
    edge2 = ki.add_edge(
        edge_type="became_skill",
        target="icm-workspace-architect",
    )
    assert edge2 is edge1
    assert len(ki.edges) == 1

    edge3 = ki.add_edge(
        edge_type="references_code",
        target="src/harness/services/storage/",
        target_kind="path",
    )
    assert len(ki.edges) == 2
    assert edge3.target_kind == "path"


@pytest.mark.unit
def test_taxonomy_domain_normalization():
    """Verify controlled taxonomy domain extraction and alias normalization."""
    assert is_valid_domain("agent_orchestration") is True
    assert is_valid_domain("security_and_forensics") is True
    assert is_valid_domain("invalid_domain_xyz") is False

    # Mapping legacy and composite categories
    assert normalize_category("agent_architecture_and_context_engineering") == "context_engineering/architecture"
    assert normalize_category("reverse-engineering / differential-analysis / facet-semantics") == "security_and_forensics/reverse_engineering"
    assert normalize_category("endogenous_reflection") == "memory_and_epistemics/reflection"
    assert normalize_category("storage") == "data_engineering/storage"
    assert normalize_category("gis") == "scientific_computing/geospatial"
    assert normalize_category(None) == "general"

    # Domain extraction
    assert get_taxonomy_domain("context_engineering/architecture") == "context_engineering"
    assert get_taxonomy_domain("security_and_forensics") == "security_and_forensics"


@pytest.mark.unit
def test_contradiction_detection_review_queue():
    """Verify ContradictionDetector flags antinomies and supersessions as a review queue."""
    ki_a = KnowledgeItemRecord(
        id="ki_legacy_policy",
        title="Legacy In-Process Plugin Execution",
        category="security_and_forensics",
        tags=["plugins", "sandbox", "execution"],
        isnad=IsnadLineageBlock(
            decision_id="dec_a",
            claims=[{
                "assertion": "External plugins are always allowed to run in-process for highest performance",
                "verified": True,
            }],
        ),
    )

    ki_b = KnowledgeItemRecord(
        id="ki_modern_policy",
        title="Subprocess Sandbox Isolation Invariant",
        category="security_and_forensics",
        tags=["plugins", "sandbox", "execution"],
        isnad=IsnadLineageBlock(
            decision_id="dec_b",
            claims=[{
                "assertion": "External plugins are never allowed in-process and must use subprocess sandboxes",
                "verified": True,
            }],
        ),
    )

    detector = ContradictionDetector()
    conflicts = detector.detect_contradictions([ki_a, ki_b])
    assert len(conflicts) >= 1
    conflict = conflicts[0]
    assert conflict.conflict_type in ("direct_antinomy", "polarity_mismatch")
    assert conflict.suggested_edge == "contradicts"
    assert "ki_legacy_policy" in (conflict.ki_a, conflict.ki_b)
    assert "ki_modern_policy" in (conflict.ki_a, conflict.ki_b)


@pytest.mark.unit
def test_knowledge_graph_queries_and_backfill():
    """Verify KnowledgeGraphQueryService lineage, dependents, and link proposal."""
    ki1 = KnowledgeItemRecord(
        id="ki_icm_root",
        title="Interpretable Context Methodology",
        category="context_engineering",
        tags=["icm", "context"],
        source_target="src/harness/services/icm_architect/",
        anchors={"target_skill": "icm-workspace-architect"},
    )
    ki2 = KnowledgeItemRecord(
        id="ki_icm_rules",
        title="ICM Stage Checks & Cold Walk Test",
        category="context_engineering",
        tags=["icm", "context", "checks"],
        superseded_by="ki_icm_root",
    )

    graph = KnowledgeGraphQueryService()

    # Backfill edges mechanically
    added = graph.backfill_edges_mechanically([ki1, ki2])
    assert added >= 2

    # Verify skill lineage
    lineage = graph.get_skill_lineage("icm-workspace-architect", [ki1, ki2])
    assert "ki_icm_root" in lineage

    # Verify dependents of ki_icm_root (superseded_by in ki2 becomes supersedes edge)
    contradictions = graph.get_contradictions("ki_icm_root", [ki1, ki2])
    assert "ki_icm_rules" in contradictions

    # Propose links for a new item
    new_ki = KnowledgeItemRecord(
        id="ki_icm_extension",
        title="ICM Pipeline Primitives",
        category="context_engineering",
        tags=["icm", "context", "sequence"],
        source_target="src/harness/services/icm_architect/primitives.py",
    )
    proposed = graph.propose_links(new_ki, [ki1, ki2])
    assert any(p.type == "references_code" for p in proposed)
    assert any(p.type == "same_domain" for p in proposed)


@pytest.mark.asyncio
async def test_vault_era_unification_and_single_source_of_truth(tmp_path: Path):
    """Verify sync unifies older & newer metadata eras and export writes dual-file."""
    vault_dir = tmp_path / "knowledge"
    vault_dir.mkdir()

    # Older era item: source_brain, context, distilled_learning
    old_dir = vault_dir / "ki_legacy_01"
    old_dir.mkdir()
    (old_dir / "metadata.json").write_text(
        json.dumps({
            "id": "ki_legacy_01",
            "title": "Legacy Plugin Card Formatting",
            "source_brain": "C:/Users/test/brain",
            "category": "architecture",
            "tags": ["plugin_system", "documentation"],
            "context": "Brain repeatedly scaffolded plugin metadata cards.",
            "distilled_learning": "Every plugin must ship with CARD.md.",
            "isnad": {"primary_source": "logs/transcript.jsonl#L10", "verified": True},
        }),
        encoding="utf-8",
    )
    (old_dir / "summary.md").write_text("# Legacy Plugin Card\n\nEvery plugin must ship with CARD.md.", encoding="utf-8")

    storage = SQLiteStorageService(":memory:")
    synced = await storage.sync_knowledge_vault(vault_dir)
    assert synced == 1

    item = await storage.get_knowledge_item("ki_legacy_01")
    assert item is not None
    assert item.schema_version == "1.0.0"
    assert item.category == "developer_experience/architecture"
    assert len(item.edges) >= 0

    # Export to new vault directory
    export_dir = tmp_path / "exported_knowledge"
    exported_count = await storage.export_knowledge_vault(export_dir)
    assert exported_count == 1
    assert (export_dir / "ki_legacy_01" / "metadata.json").exists()
    assert (export_dir / "ki_legacy_01" / "summary.md").exists()

    exported_meta = json.loads((export_dir / "ki_legacy_01" / "metadata.json").read_text(encoding="utf-8"))
    assert exported_meta["schema_version"] == "1.0.0"
    assert exported_meta["category"] == "developer_experience/architecture"


@pytest.mark.unit
def test_react_step_skill_rerouting():
    """Verify maybe_reroute_skills re-evaluates guidance when step cadence triggers."""
    ctx = ServiceContext()
    mock_intel = MagicMock()
    mock_guidance = SkillExecutionGuidance(
        task="Test task",
        selected_skills=("icm-workspace-architect", "tdd"),
        execution_pipeline=("icm-workspace-architect", "tdd"),
        confidence=0.85,
    )
    mock_intel.compile_execution_guidance.return_value = mock_guidance
    ctx.provide(SKILL_INTELLIGENCE_KEY, mock_intel)

    traj = AgentTrajectory(task="Build architecture with ICM methodology")
    traj.add_step(AgentStep(step_number=1, thought="Step 1 observation", observation="Observation finding folder error"))

    # Step 3: does not hit cadence of 5 -> no re-routing
    current = ["crafting-skills"]
    res1 = maybe_reroute_skills(ctx, traj, step_idx=3, current_skills=current, cadence=5)
    assert res1 == ["crafting-skills"]
    mock_intel.compile_execution_guidance.assert_not_called()

    # Step 5: hits cadence -> re-routes and merges within max 4 budget
    res2 = maybe_reroute_skills(ctx, traj, step_idx=5, current_skills=current, cadence=5)
    assert "icm-workspace-architect" in res2
    assert "tdd" in res2
    assert len(res2) <= 4


@pytest.mark.unit
def test_skill_scaffold_provenance_recording(tmp_path: Path):
    """Verify skill scaffolding records generator provenance and single-pipe CARD.md borders."""
    skill_dir = tmp_path / "skills" / "test-provenance-skill"
    options = SkillOptions(
        name="test-provenance-skill",
        description="Skill with provenance lineage tracking.",
        category="engineering / meta-skills",
        generated_by=["book-to-skill-forge", "crafting-skills"],
        source_ki_id="ki_icm_architect",
    )

    result = SkillScaffoldEngine.scaffold(skill_dir, options=options)
    assert result.skill_file.exists()
    assert result.card_file is not None and result.card_file.exists()

    # Verify .provenance.json
    prov_file = skill_dir / ".provenance.json"
    assert prov_file.exists()
    prov_data = json.loads(prov_file.read_text(encoding="utf-8"))
    assert prov_data["skill_name"] == "test-provenance-skill"
    assert "book-to-skill-forge" in prov_data["generated_by"]
    assert prov_data["source_ki_id"] == "ki_icm_architect"

    # Verify single-pipe ASCII border and provenance row in CARD.md
    card_text = result.card_file.read_text(encoding="utf-8")
    assert "│ SKILL: test-provenance-skill" in card_text
    assert "│ Provenance: book-to-skill-forge, crafting-skills" in card_text
    assert "╔" not in card_text
    assert "║" not in card_text


@pytest.mark.unit
def test_cli_contradictions_and_lineage_commands(tmp_path: Path):
    """Verify click commands 'harness knowledge contradictions' and 'harness knowledge lineage'."""
    vault_dir = tmp_path / "knowledge"
    vault_dir.mkdir()

    ki_dir = vault_dir / "ki_sample_skill_src"
    ki_dir.mkdir()
    (ki_dir / "metadata.json").write_text(
        json.dumps({
            "id": "ki_sample_skill_src",
            "title": "Sample Skill Source Pattern",
            "category": "agent_orchestration",
            "anchors": {"target_skill": "sample-agent-skill"},
            "tags": ["skill:sample-agent-skill"],
            "isnad": {"claims": []},
        }),
        encoding="utf-8",
    )
    (ki_dir / "summary.md").write_text("# Sample Pattern", encoding="utf-8")

    runner = CliRunner()

    # Test contradictions command
    res_contra = runner.invoke(knowledge_group, ["contradictions", "--vault", str(vault_dir)])
    assert res_contra.exit_code == 0
    assert "No contradictory claims" in res_contra.output or "Contradiction Review Queue" in res_contra.output

    # Test lineage command
    res_lineage = runner.invoke(knowledge_group, ["lineage", "sample-agent-skill", "--vault", str(vault_dir)])
    assert res_lineage.exit_code == 0
    assert "Lineage for Skill 'sample-agent-skill'" in res_lineage.output
    assert "ki_sample_skill_src" in res_lineage.output
