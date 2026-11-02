"""Regression and contract tests for Knowledge Vault data integrity, key preservation, and learning loop (Track 0)."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.creator.skills.models import SkillOptions
from harness.creator.skills.scaffold import SkillScaffoldEngine
from harness.services.storage import (
    KnowledgeItemRecord,
    SQLiteStorageService,
)


@pytest.mark.unit
class TestKnowledgeVaultDataIntegrity:
    """Verifies lossless metadata preservation and learning-loop outcome tracking."""

    @pytest.mark.asyncio
    async def test_fresh_directory_export_preserves_historical_keys(self, tmp_path: Path) -> None:
        """Assert that exporting to a fresh directory preserves historical keys and summary bytes."""
        src_vault = Path(".harness/knowledge")
        if not src_vault.exists():
            pytest.skip(".harness/knowledge not found")

        storage = SQLiteStorageService(":memory:")
        synced_count = await storage.sync_knowledge_vault(src_vault)
        assert synced_count >= 282

        target_vault = tmp_path / "fresh_export"
        exported_count = await storage.export_knowledge_vault(target_vault)
        assert exported_count == synced_count

        # Spot-check headroom item for source dict and distilled_learning preservation
        headroom_src = json.loads((src_vault / "ki_20261028_headroom_context_optimization" / "metadata.json").read_text(encoding="utf-8"))
        headroom_dst = json.loads((target_vault / "ki_20261028_headroom_context_optimization" / "metadata.json").read_text(encoding="utf-8"))

        assert "source" in headroom_dst
        assert headroom_dst["source"]["url"] == headroom_src["source"]["url"]
        assert headroom_dst["distilled_learning"] == headroom_src["distilled_learning"]

        # Check all items in source vault: all keys in src must be in dst
        for ki_dir in src_vault.iterdir():
            if not ki_dir.is_dir():
                continue
            src_meta = json.loads((ki_dir / "metadata.json").read_text(encoding="utf-8"))
            dst_meta = json.loads((target_vault / ki_dir.name / "metadata.json").read_text(encoding="utf-8"))

            for key in src_meta:
                if key in ("claims", "isnad_claims"):
                    assert "isnad" in dst_meta
                    continue
                if key == "ki_id":
                    assert "id" in dst_meta
                    continue
                assert key in dst_meta, f"Key '{key}' was stripped in fresh export of {ki_dir.name}"

            src_sum = ki_dir / "summary.md"
            if src_sum.exists():
                dst_sum = target_vault / ki_dir.name / "summary.md"
                assert dst_sum.exists()
                assert len(dst_sum.read_bytes()) == len(src_sum.read_bytes())

        # Re-sync from fresh target vault
        storage_fresh = SQLiteStorageService(":memory:")
        resynced = await storage_fresh.sync_knowledge_vault(target_vault)
        assert resynced == synced_count
        storage.close()
        storage_fresh.close()

    @pytest.mark.asyncio
    async def test_sync_strict_mode_and_skipped_reporting(self, tmp_path: Path) -> None:
        """Verify strict mode fails loudly on invalid items, and skipped items are tracked."""
        vault_dir = tmp_path / "test_vault"
        vault_dir.mkdir(parents=True)

        valid_dir = vault_dir / "ki_valid"
        valid_dir.mkdir()
        (valid_dir / "metadata.json").write_text(json.dumps({
            "id": "ki_valid",
            "title": "Valid Item",
            "category": "developer_experience",
            "tags": ["test"],
        }), encoding="utf-8")
        (valid_dir / "summary.md").write_text("Valid summary", encoding="utf-8")

        corrupt_dir = vault_dir / "ki_corrupt"
        corrupt_dir.mkdir()
        (corrupt_dir / "metadata.json").write_text("{invalid json", encoding="utf-8")

        storage = SQLiteStorageService(":memory:")
        # Non-strict mode should sync valid item and record skipped item
        count = await storage.sync_knowledge_vault(vault_dir, strict=False)
        assert count == 1
        skipped = storage.get_last_skipped_items()
        assert len(skipped) == 1
        assert skipped[0][0] == "ki_corrupt"

        # Strict mode must raise ValueError
        with pytest.raises(ValueError, match="Sync failed in strict mode with 1 skipped item"):
            await storage.sync_knowledge_vault(vault_dir, strict=True)

        storage.close()

    @pytest.mark.asyncio
    async def test_knowledge_outcome_increments_success_count_on_bare_context(self, tmp_path: Path) -> None:
        """Verify record_knowledge_outcome persists success_count even without cached memory item."""
        vault_dir = tmp_path / "test_vault"
        vault_dir.mkdir(parents=True)

        ki_dir = vault_dir / "ki_retrieval_test"
        ki_dir.mkdir()
        (ki_dir / "metadata.json").write_text(json.dumps({
            "id": "ki_retrieval_test",
            "title": "Retrieval Test Pattern",
            "category": "developer_experience",
            "tags": ["testing", "react"],
            "retrieval_count": 0,
            "success_count": 0,
            "status": "ACTIVE",
        }), encoding="utf-8")
        (ki_dir / "summary.md").write_text("Retrieval test summary", encoding="utf-8")

        storage = SQLiteStorageService(":memory:")
        await storage.record_knowledge_retrieval(["ki_retrieval_test"], vault_dir=vault_dir)

        meta_after_ret = json.loads((ki_dir / "metadata.json").read_text(encoding="utf-8"))
        assert meta_after_ret["retrieval_count"] == 1

        # Use a fresh, completely empty storage service simulating a separate step/process
        fresh_storage = SQLiteStorageService(":memory:")
        await fresh_storage.record_knowledge_outcome(["ki_retrieval_test"], success=True, vault_dir=vault_dir)

        meta_after_outcome = json.loads((ki_dir / "metadata.json").read_text(encoding="utf-8"))
        assert meta_after_outcome["success_count"] == 1

        storage.close()
        fresh_storage.close()

    @pytest.mark.asyncio
    async def test_reflector_engine_hydrates_propose_links(self, tmp_path: Path) -> None:
        """Verify HarnessReflectorEngine hydrates existing items from vault_dir to propose links."""
        vault_dir = tmp_path / "fixture_vault"
        vault_dir.mkdir(parents=True)
        ki_existing = vault_dir / "ki_arch_existing"
        ki_existing.mkdir()
        (ki_existing / "metadata.json").write_text(json.dumps({
            "id": "ki_arch_existing",
            "title": "Existing Architecture Pattern",
            "category": "developer_experience/architecture",
            "tags": ["developer_experience/architecture", "endogenous_memory"],
            "edges": [],
        }), encoding="utf-8")
        (ki_existing / "summary.md").write_text("Existing pattern", encoding="utf-8")

        from harness.creator.reflection.models import DistilledHeuristic
        from harness.creator.reflection.engine import HarnessReflectorEngine

        class MockPipeline:
            def distill(self, reports, transcripts, scope=None):
                return [
                    DistilledHeuristic(
                        title="New Architecture Heuristic",
                        category="developer_experience/architecture",
                        confidence=0.95,
                        heuristic="Always test before commit.",
                        anti_pattern="Skipping tests.",
                    )
                ]

        storage = SQLiteStorageService(":memory:")
        engine = HarnessReflectorEngine(storage=storage, pipeline=MockPipeline())

        report = await engine.reflect(
            commit_to_vault=True,
            generate_html_brief=False,
            vault_dir=vault_dir,
        )

        assert len(report.knowledge_items) == 1
        new_ki = report.knowledge_items[0]
        # Should have received same_domain edge to ki_arch_existing
        assert any(e.type == "same_domain" and e.target == "ki_arch_existing" for e in new_ki.edges)
        storage.close()

    def test_skill_scaffold_custom_vault_dir(self, tmp_path: Path) -> None:
        """Verify SkillScaffoldEngine appends became_skill edge to source KI in custom vault."""
        vault_dir = tmp_path / "custom_vault"
        vault_dir.mkdir(parents=True)
        ki_dir = vault_dir / "ki_source_01"
        ki_dir.mkdir()
        (ki_dir / "metadata.json").write_text(json.dumps({
            "id": "ki_source_01",
            "title": "Source KI Pattern",
            "category": "developer_experience",
            "tags": ["scaffold"],
            "edges": [],
        }), encoding="utf-8")
        (ki_dir / "summary.md").write_text("Source summary", encoding="utf-8")

        skills_dir = tmp_path / ".agents" / "skills"
        opts = SkillOptions(
            name="custom-scaffolded-skill",
            description="Testing custom vault dir scaffold",
            source_ki_id="ki_source_01",
            vault_dir=vault_dir,
            auto_validate=False,
        )

        res = SkillScaffoldEngine.scaffold(skills_dir, opts)
        assert res.skill_file.exists()

        # Check that metadata.json in custom_vault was updated with became_skill edge
        updated_meta = json.loads((ki_dir / "metadata.json").read_text(encoding="utf-8"))
        edges = updated_meta.get("edges", [])
        assert len(edges) == 1
        assert edges[0]["type"] == "became_skill"
        assert edges[0]["target"] == "custom-scaffolded-skill"
        assert edges[0]["derived"] is False
