"""Contract test suite for edge backfilling, save-path linking, and round-trip idempotency."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
import pytest

from harness.commands.reflection import knowledge_backfill
from harness.creator.skills import SkillOptions, SkillScaffoldEngine
from harness.services.storage import (
    KnowledgeEdge,
    KnowledgeItemRecord,
    SQLiteStorageService,
    backfill_edges_mechanically,
    propose_links,
)


@pytest.fixture
def fixture_backfill_vault(tmp_path: Path) -> Path:
    """Fixture vault containing items with latent code references, target skills, and historical extra keys."""
    vault_dir = tmp_path / ".harness" / "knowledge"
    vault_dir.mkdir(parents=True)

    # Item 1: source_target in src/ + historical keys (context, provenance)
    ki1 = vault_dir / "ki_kernel_core"
    ki1.mkdir()
    (ki1 / "metadata.json").write_text(json.dumps({
        "id": "ki_kernel_core",
        "title": "Kernel Core Engine Pattern",
        "category": "developer_experience/architecture",
        "tags": ["kernel", "ioc", "service_key"],
        "source_target": "src/harness/kernel/core.py",
        "context": "Cycle 70 architectural review",
        "provenance": {"origin": "deep-repo-auditor", "git_commit": "77ceb2f"},
        "edges": [],
    }), encoding="utf-8")
    (ki1 / "summary.md").write_text("Kernel core pattern summary", encoding="utf-8")

    # Item 2: anchors.target_skill + references array with skill and code path
    ki2 = vault_dir / "ki_skill_scaffolder"
    ki2.mkdir()
    (ki2 / "metadata.json").write_text(json.dumps({
        "id": "ki_skill_scaffolder",
        "title": "Skill Scaffold Engine",
        "category": "agent_orchestration/skills",
        "tags": ["skills", "scaffold", "craft"],
        "anchors": {"target_skill": "agent-skills-architect"},
        "references": [
            {"path": ".agents/skills/agent-skills-architect/SKILL.md", "description": "Skill spec"},
            {"path": "src/harness/creator/skills/scaffold.py", "description": "Scaffold engine"},
        ],
        "edges": [],
    }), encoding="utf-8")
    (ki2 / "summary.md").write_text("Skill scaffold summary", encoding="utf-8")

    # Item 3: plugins_scaffolded list
    ki3 = vault_dir / "ki_bridge_plugin"
    ki3.mkdir()
    (ki3 / "metadata.json").write_text(json.dumps({
        "id": "ki_bridge_plugin",
        "title": "Bridge Plugin Scaffolding",
        "category": "data_engineering/storage",
        "tags": ["bridge", "plugin"],
        "plugins_scaffolded": ["plugin.google_adk_runtime"],
        "edges": [],
    }), encoding="utf-8")
    (ki3 / "summary.md").write_text("Bridge plugin summary", encoding="utf-8")

    # Item 4: supersedes relationship (superseded_by pointing to ki_kernel_core)
    ki4 = vault_dir / "ki_legacy_core"
    ki4.mkdir()
    (ki4 / "metadata.json").write_text(json.dumps({
        "id": "ki_legacy_core",
        "title": "Legacy Kernel Core",
        "category": "developer_experience/architecture",
        "tags": ["kernel", "legacy"],
        "superseded_by": "ki_kernel_core",
        "edges": [],
    }), encoding="utf-8")
    (ki4 / "summary.md").write_text("Legacy kernel summary", encoding="utf-8")

    # Item 5: same_domain peer with ki_kernel_core (shares 2 non-mega tags: kernel, ioc)
    ki5 = vault_dir / "ki_ioc_container"
    ki5.mkdir()
    (ki5 / "metadata.json").write_text(json.dumps({
        "id": "ki_ioc_container",
        "title": "IoC Container Pattern",
        "category": "developer_experience/architecture",
        "tags": ["kernel", "ioc", "container"],
        "edges": [],
    }), encoding="utf-8")
    (ki5 / "summary.md").write_text("IoC container summary", encoding="utf-8")

    return vault_dir


@pytest.mark.unit
class TestKnowledgeBackfillAndWiring:
    """Verifies mechanical backfilling, save-path wiring, and round-trip idempotency."""

    def test_propose_links_algorithm(self) -> None:
        """Verify candidate link proposal for newly formulated Knowledge Item."""
        existing = [
            KnowledgeItemRecord(
                id="ki_prev_01",
                title="Existing Pattern",
                category="developer_experience/architecture",
                tags=["arch", "submodules"],
            )
        ]

        new_ki = KnowledgeItemRecord(
            id="ki_new",
            title="New Architecture Pattern",
            category="developer_experience/architecture",
            tags=["arch", "submodules", "new"],
            source_target="src/harness/services/storage/sqlite.py",
            anchors={"target_skill": "architecture-deepening-workflow"},
        )

        proposed = propose_links(new_ki, existing)
        p_types = {p.type for p in proposed}
        assert "references_code" in p_types
        assert "became_skill" in p_types
        assert "same_domain" in p_types

        # Verify edge targets
        code_edge = next(p for p in proposed if p.type == "references_code")
        assert code_edge.target == "src/harness/services/storage/sqlite.py"
        assert code_edge.target_kind == "path"

        skill_edge = next(p for p in proposed if p.type == "became_skill")
        assert skill_edge.target == "architecture-deepening-workflow"
        assert skill_edge.target_kind == "skill"

    @pytest.mark.asyncio
    async def test_roundtrip_idempotency_and_historical_key_retention(
        self, fixture_backfill_vault: Path
    ) -> None:
        """Verify: sync -> backfill --commit -> re-sync -> re-backfill produces 0 duplicates and retains keys."""
        runner = CliRunner()

        # Step 1: Execute backfill with --commit
        res1 = runner.invoke(knowledge_backfill, [
            "--vault", str(fixture_backfill_vault),
            "--commit",
        ])
        assert res1.exit_code == 0, res1.output
        assert "COMMITTED to" in res1.output

        # Step 2: Verify on-disk metadata of ki_kernel_core
        meta1_path = fixture_backfill_vault / "ki_kernel_core" / "metadata.json"
        meta1_data = json.loads(meta1_path.read_text(encoding="utf-8"))

        # Verify historical keys are preserved!
        assert meta1_data.get("context") == "Cycle 70 architectural review"
        assert meta1_data.get("provenance", {}).get("origin") == "deep-repo-auditor"

        # Verify backfilled edges on ki_kernel_core
        edge_types1 = [e["type"] for e in meta1_data["edges"]]
        assert "references_code" in edge_types1
        assert "supersedes" in edge_types1
        # Directed: ki_kernel_core supersedes ki_legacy_core
        supersedes_edge = next(e for e in meta1_data["edges"] if e["type"] == "supersedes")
        assert supersedes_edge["target"] == "ki_legacy_core"

        # Verify ki_skill_scaffolder has became_skill and references_code
        meta2_data = json.loads((fixture_backfill_vault / "ki_skill_scaffolder" / "metadata.json").read_text(encoding="utf-8"))
        edge_types2 = [e["type"] for e in meta2_data["edges"]]
        assert "became_skill" in edge_types2
        assert "references_code" in edge_types2

        # Verify ki_bridge_plugin has became_plugin
        meta3_data = json.loads((fixture_backfill_vault / "ki_bridge_plugin" / "metadata.json").read_text(encoding="utf-8"))
        edge_types3 = [e["type"] for e in meta3_data["edges"]]
        assert "became_plugin" in edge_types3

        total_edges_pass1 = sum(
            len(json.loads((fixture_backfill_vault / d.name / "metadata.json").read_text(encoding="utf-8")).get("edges", []))
            for d in fixture_backfill_vault.iterdir() if d.is_dir()
        )
        assert total_edges_pass1 > 0

        # Step 3: Run second backfill with --commit (IDEMPOTENCY ASSERTION)
        res2 = runner.invoke(knowledge_backfill, [
            "--vault", str(fixture_backfill_vault),
            "--commit",
        ])
        assert res2.exit_code == 0
        assert "Edges Added / Proposed:0" in res2.output

        total_edges_pass2 = sum(
            len(json.loads((fixture_backfill_vault / d.name / "metadata.json").read_text(encoding="utf-8")).get("edges", []))
            for d in fixture_backfill_vault.iterdir() if d.is_dir()
        )
        # Invariant: exactly 0 duplicate edges added on second pass
        assert total_edges_pass2 == total_edges_pass1

    def test_skill_scaffold_source_ki_wiring(self, tmp_path: Path) -> None:
        """Verify SkillScaffoldEngine.scaffold writes became_skill edge back to source KI."""
        vault_dir = tmp_path / ".harness" / "knowledge"
        vault_dir.mkdir(parents=True)
        ki_dir = vault_dir / "ki_source_test"
        ki_dir.mkdir()
        (ki_dir / "metadata.json").write_text(json.dumps({
            "id": "ki_source_test",
            "title": "Source Pattern for Skill",
            "edges": [],
        }), encoding="utf-8")

        # Monkeypatch current working directory knowledge vault path or relative
        import os
        old_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        try:
            skills_dir = tmp_path / ".agents" / "skills" / "test-deep-skill"
            opts = SkillOptions(
                name="test-deep-skill",
                source_ki_id="ki_source_test",
                description="Test deep skill",
            )
            SkillScaffoldEngine.scaffold(skills_dir, options=opts)

            # Verify source KI metadata received became_skill edge!
            updated_ki = json.loads((ki_dir / "metadata.json").read_text(encoding="utf-8"))
            edges = updated_ki.get("edges", [])
            assert len(edges) == 1
            assert edges[0]["type"] == "became_skill"
            assert edges[0]["target"] == "test-deep-skill"
            assert edges[0]["target_kind"] == "skill"
            assert edges[0]["derived"] is False
        finally:
            os.chdir(old_cwd)

