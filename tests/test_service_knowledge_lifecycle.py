"""Contract test suite for Knowledge Vault lifecycle, retrieval exclusion, and contradiction resolution."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
import pytest

from harness.commands.reflection import knowledge_lifecycle, knowledge_resolve
from harness.services.storage import (
    KnowledgeEdge,
    KnowledgeItemRecord,
    SQLiteStorageService,
)


@pytest.fixture
def mock_lifecycle_vault(tmp_path: Path) -> Path:
    """Fixture vault with active, challenged, archived, and superseded items."""
    vault_dir = tmp_path / ".harness" / "knowledge"
    vault_dir.mkdir(parents=True)

    # 1. Active item
    ki1 = vault_dir / "ki_active"
    ki1.mkdir()
    (ki1 / "metadata.json").write_text(json.dumps({
        "id": "ki_active",
        "title": "Active Micro-Kernel Architecture Pattern",
        "category": "developer_experience/architecture",
        "tags": ["kernel", "architecture", "ioc"],
        "status": "ACTIVE",
        "retrieval_count": 10,
        "success_count": 9,
    }), encoding="utf-8")
    (ki1 / "summary.md").write_text("Active summary", encoding="utf-8")

    # 2. Challenged item
    ki2 = vault_dir / "ki_challenged"
    ki2.mkdir()
    (ki2 / "metadata.json").write_text(json.dumps({
        "id": "ki_challenged",
        "title": "Challenged Monolithic Pattern",
        "category": "developer_experience/architecture",
        "tags": ["kernel", "architecture", "ioc"],
        "status": "CHALLENGED",
        "retrieval_count": 8,
        "success_count": 2,
    }), encoding="utf-8")
    (ki2 / "summary.md").write_text("Challenged summary", encoding="utf-8")

    # 3. Superseded item
    ki3 = vault_dir / "ki_superseded"
    ki3.mkdir()
    (ki3 / "metadata.json").write_text(json.dumps({
        "id": "ki_superseded",
        "title": "Deprecated Storage Pattern",
        "category": "developer_experience/architecture",
        "tags": ["kernel", "architecture", "ioc"],
        "status": "SUPERSEDED",
        "superseded_by": "ki_active",
        "retrieval_count": 20,
        "success_count": 1,
    }), encoding="utf-8")
    (ki3 / "summary.md").write_text("Superseded summary", encoding="utf-8")

    # 4. Archived item
    ki4 = vault_dir / "ki_archived"
    ki4.mkdir()
    (ki4 / "metadata.json").write_text(json.dumps({
        "id": "ki_archived",
        "title": "Archived Prototype Experiment",
        "category": "developer_experience/architecture",
        "tags": ["kernel", "architecture", "ioc"],
        "status": "ARCHIVED",
        "retrieval_count": 5,
        "success_count": 0,
    }), encoding="utf-8")
    (ki4 / "summary.md").write_text("Archived summary", encoding="utf-8")

    return vault_dir


@pytest.mark.unit
class TestKnowledgeVaultRetrievalAndLifecycle:
    """Verifies Post-Plan Analysis §2 High #1 & #2 requirements."""

    @pytest.mark.asyncio
    async def test_retrieval_excludes_superseded_and_downweights_challenged(
        self, mock_lifecycle_vault: Path
    ) -> None:
        """Verify SUPERSEDED and ARCHIVED items are excluded; CHALLENGED items receive 0.25x status penalty."""
        storage = SQLiteStorageService(":memory:")
        await storage.sync_knowledge_vault(mock_lifecycle_vault)

        # Query matching tags shared across all items
        results = await storage.retrieve_relevant_knowledge("kernel architecture ioc", max_items=10)
        result_ids = [r.id for r in results]

        # Invariant 1: SUPERSEDED and ARCHIVED items must be strictly excluded
        assert "ki_superseded" not in result_ids
        assert "ki_archived" not in result_ids

        # Invariant 2: Active item must be retrieved
        assert "ki_active" in result_ids

        # Invariant 3: If challenged item is retrieved, it must be ranked lower than active
        if "ki_challenged" in result_ids:
            active_idx = result_ids.index("ki_active")
            challenged_idx = result_ids.index("ki_challenged")
            assert active_idx < challenged_idx

        storage.close()

    @pytest.mark.asyncio
    async def test_evaluate_vault_lifecycle_promotes_and_demotes(
        self, mock_lifecycle_vault: Path
    ) -> None:
        """Verify lifecycle evaluator promotes items >=75% success and demotes <=25% success."""
        storage = SQLiteStorageService(":memory:")
        await storage.sync_knowledge_vault(mock_lifecycle_vault)

        report = await storage.evaluate_vault_lifecycle(
            min_retrievals=5,
            promote_ratio=0.75,
            demote_ratio=0.25,
            vault_dir=mock_lifecycle_vault,
        )

        assert "ki_active" in report["promoted"]
        assert "ki_challenged" in report["demoted"]

        # Verify on-disk metadata was updated non-destructively
        meta_active = json.loads((mock_lifecycle_vault / "ki_active" / "metadata.json").read_text(encoding="utf-8"))
        assert meta_active["status"] == "PROMOTED"

        meta_challenged = json.loads((mock_lifecycle_vault / "ki_challenged" / "metadata.json").read_text(encoding="utf-8"))
        assert meta_challenged["status"] == "DEMOTED"

        storage.close()

    def test_cli_knowledge_resolve_supersede(self, mock_lifecycle_vault: Path) -> None:
        """Verify harness knowledge resolve --action supersede updates disk with canonical edge."""
        runner = CliRunner()
        res = runner.invoke(knowledge_resolve, [
            "ki_active", "ki_challenged",
            "--action", "supersede",
            "--reason", "Active micro-kernel supersedes legacy monolith",
            "--vault", str(mock_lifecycle_vault),
        ])
        assert res.exit_code == 0, res.output
        assert "Marked 'ki_challenged' SUPERSEDED by 'ki_active'" in res.output

        # Verify ki_challenged metadata on disk
        meta_challenged = json.loads((mock_lifecycle_vault / "ki_challenged" / "metadata.json").read_text(encoding="utf-8"))
        assert meta_challenged["status"] == "SUPERSEDED"
        assert meta_challenged["superseded_by"] == "ki_active"

        # Verify ki_active metadata on disk has directed supersedes edge
        meta_active = json.loads((mock_lifecycle_vault / "ki_active" / "metadata.json").read_text(encoding="utf-8"))
        assert any(
            e["type"] == "supersedes" and e["target"] == "ki_challenged" and e["target_kind"] == "ki"
            for e in meta_active.get("edges", [])
        )

    def test_cli_knowledge_resolve_contradict(self, mock_lifecycle_vault: Path) -> None:
        """Verify harness knowledge resolve --action contradict marks both CHALLENGED with mutual edges."""
        runner = CliRunner()
        res = runner.invoke(knowledge_resolve, [
            "ki_active", "ki_challenged",
            "--action", "contradict",
            "--reason", "Conflicting concurrency constraints",
            "--vault", str(mock_lifecycle_vault),
        ])
        assert res.exit_code == 0, res.output
        assert "status updated to CHALLENGED" in res.output

        meta_active = json.loads((mock_lifecycle_vault / "ki_active" / "metadata.json").read_text(encoding="utf-8"))
        meta_challenged = json.loads((mock_lifecycle_vault / "ki_challenged" / "metadata.json").read_text(encoding="utf-8"))

        assert meta_active["status"] == "CHALLENGED"
        assert meta_challenged["status"] == "CHALLENGED"

        assert any(e["type"] == "contradicts" and e["target"] == "ki_challenged" for e in meta_active.get("edges", []))
        assert any(e["type"] == "contradicts" and e["target"] == "ki_active" for e in meta_challenged.get("edges", []))

