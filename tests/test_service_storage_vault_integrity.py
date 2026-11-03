"""Regression and contract tests for Knowledge Vault data integrity, key preservation, and learning loop (Track 0)."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.creator.skills.models import SkillOptions
from harness.creator.skills.scaffold import SkillScaffoldEngine
from harness.services.storage import (
    DerivedKnowledgeGraph,
    KnowledgeGraphNode,
    KnowledgeGraphSummary,
    KnowledgeItemRecord,
    SQLiteStorageService,
    export_cypher,
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

    @pytest.mark.asyncio
    async def test_knowledge_lifecycle_promotion_e2e_proof(self, tmp_path: Path) -> None:
        """Track 7: Prove evaluate_vault_lifecycle transitions ACTIVE -> PROMOTED in SQLite and on disk."""
        vault_dir = tmp_path / "lifecycle_vault"
        vault_dir.mkdir(parents=True)

        # 1. High utility item: 5 retrievals, 4 successes (ratio = 0.80 >= 0.75)
        ki_promote = vault_dir / "ki_candidate_promote"
        ki_promote.mkdir()
        (ki_promote / "metadata.json").write_text(json.dumps({
            "id": "ki_candidate_promote",
            "title": "Promotion Candidate",
            "category": "developer_experience",
            "tags": ["lifecycle", "verified"],
            "status": "ACTIVE",
            "retrieval_count": 5,
            "success_count": 4,
        }), encoding="utf-8")
        (ki_promote / "summary.md").write_text("Promotion candidate summary", encoding="utf-8")

        # 2. Low utility item: 6 retrievals, 1 success (ratio = 0.166 <= 0.25)
        ki_demote = vault_dir / "ki_candidate_demote"
        ki_demote.mkdir()
        (ki_demote / "metadata.json").write_text(json.dumps({
            "id": "ki_candidate_demote",
            "title": "Demotion Candidate",
            "category": "developer_experience",
            "tags": ["lifecycle", "stale"],
            "status": "ACTIVE",
            "retrieval_count": 6,
            "success_count": 1,
        }), encoding="utf-8")
        (ki_demote / "summary.md").write_text("Demotion candidate summary", encoding="utf-8")

        # 3. Insufficient retrievals item: 3 retrievals, 3 successes (ratio = 1.0 but retrievals < 5)
        ki_ignore = vault_dir / "ki_candidate_ignore"
        ki_ignore.mkdir()
        (ki_ignore / "metadata.json").write_text(json.dumps({
            "id": "ki_candidate_ignore",
            "title": "Ignore Candidate",
            "category": "developer_experience",
            "tags": ["lifecycle"],
            "status": "ACTIVE",
            "retrieval_count": 3,
            "success_count": 3,
        }), encoding="utf-8")
        (ki_ignore / "summary.md").write_text("Ignore candidate summary", encoding="utf-8")

        storage = SQLiteStorageService(":memory:")
        await storage.sync_knowledge_vault(vault_dir)

        # Execute lifecycle evaluation
        res = await storage.evaluate_vault_lifecycle(
            min_retrievals=5,
            promote_ratio=0.75,
            demote_ratio=0.25,
            vault_dir=vault_dir,
        )

        assert res["promoted"] == ["ki_candidate_promote"]
        assert res["demoted"] == ["ki_candidate_demote"]

        # Assert in SQLite storage
        item_promoted = await storage.get_knowledge_item("ki_candidate_promote")
        assert item_promoted is not None
        assert item_promoted.status == "PROMOTED"

        item_demoted = await storage.get_knowledge_item("ki_candidate_demote")
        assert item_demoted is not None
        assert item_demoted.status == "DEMOTED"

        item_ignored = await storage.get_knowledge_item("ki_candidate_ignore")
        assert item_ignored is not None
        assert item_ignored.status == "ACTIVE"

        # Assert on-disk metadata.json was mutated atomically
        meta_promoted = json.loads((ki_promote / "metadata.json").read_text(encoding="utf-8"))
        assert meta_promoted["status"] == "PROMOTED"

        meta_demoted = json.loads((ki_demote / "metadata.json").read_text(encoding="utf-8"))
        assert meta_demoted["status"] == "DEMOTED"

        meta_ignored = json.loads((ki_ignore / "metadata.json").read_text(encoding="utf-8"))
        assert meta_ignored["status"] == "ACTIVE"

        # Assert idempotency on second run
        res_repeat = await storage.evaluate_vault_lifecycle(
            min_retrievals=5,
            promote_ratio=0.75,
            demote_ratio=0.25,
            vault_dir=vault_dir,
        )
        assert res_repeat["promoted"] == []
        assert res_repeat["demoted"] == []

        storage.close()

    def test_cypher_export_isnad_claim_7tuple_properties(self, tmp_path: Path) -> None:
        """Track 7: Verify Cypher exports emit IsnadClaim nodes with full 7-tuple temporal evidence properties."""
        out_file = tmp_path / "test_epistemic_export.cypher"

        node = KnowledgeGraphNode(
            id="ki_arch_001",
            label="Empirical Harness Architecture",
            node_kind="ki",
            category="agent_orchestration",
            domain="agent_orchestration",
            tags=("harness", "react"),
            status="PROMOTED",
            retrieval_count=12,
            success_count=10,
        )
        summary = KnowledgeGraphSummary(
            total_nodes=1,
            ki_nodes=1,
            non_ki_nodes_by_kind={},
            total_edges=0,
            edges_by_type={},
            derived_edge_count=0,
            asserted_edge_count=0,
            component_count=1,
            largest_component_size=1,
            isolated_ki_count=0,
            untagged_ki_count=0,
            uncategorized_ki_count=0,
            date_coverage_count=1,
            date_sources={},
            excluded_mega_tags=(),
            ki_only_component_count=1,
            ki_only_largest_component_size=1,
            ki_only_isolated_count=0,
        )
        graph = DerivedKnowledgeGraph(nodes=(node,), edges=(), summary=summary)

        # Mock item with typed IsnadClaim containing all 7 temporal evidence properties
        class MockItem:
            id = "ki_arch_001"
            isnad = {
                "claims": [
                    {
                        "claim_id": "ki_arch_001-c1",
                        "assertion": "Deterministic 3-pass pruning bounds context budgets without semantic loss.",
                        "status": "VERIFIED",
                        "confidence": 0.98,
                        "evidence_type": "empirical_benchmark",
                        "source": "tests/test_context_pruner.py#L40-L80",
                        "verified": True,
                        "verified_by": "pytest-suite-runner",
                    }
                ]
            }

        written = export_cypher(graph, out_file, items=[MockItem()])
        assert written == out_file.resolve()
        assert out_file.exists()

        content = out_file.read_text(encoding="utf-8")

        # 1. Constraint assertion
        assert "CREATE CONSTRAINT claim_id_unique IF NOT EXISTS FOR (c:IsnadClaim) REQUIRE c.id IS UNIQUE;" in content

        # 2. Node Materialization with 7-tuple properties
        expected_claim_merge = 'MERGE (c:IsnadClaim {id: "ki_arch_001-c1"})'
        assert expected_claim_merge in content

        # 7-tuple temporal evidence assertions
        assert 'c.assertion = "Deterministic 3-pass pruning bounds context budgets without semantic loss."' in content
        assert 'c.status = "VERIFIED"' in content
        assert "c.confidence = 0.98" in content
        assert 'c.evidence_type = "empirical_benchmark"' in content
        assert 'c.source = "tests/test_context_pruner.py#L40-L80"' in content
        assert "c.verified = true" in content
        assert 'c.verified_by = "pytest-suite-runner"' in content

        # 3. Directed relationship edge
        expected_rel = 'MATCH (k:KnowledgeItem {id: "ki_arch_001"}), (c:IsnadClaim {id: "ki_arch_001-c1"}) MERGE (k)-[:ASSERTS_CLAIM]->(c);'
        assert expected_rel in content
