"""Contract test suite for StorageService decomposition per AGENTS.md Rule 11, Rule 18, Rule 40, Rule 45, Rule 58."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.kernel.context import ServiceContext
from harness.services.storage import (
    KNOWLEDGE_VAULT_KEY,
    STORAGE_SERVICE_KEY,
    IsnadAuditMixin,
    IsnadLineageBlock,
    IsnadLineageNode,
    KnowledgeItemRecord,
    KnowledgeVaultMixin,
    SQLiteStorageService,
    StoragePlugin,
    StorageService,
    plugin,
    resolve_knowledge_vault,
    resolve_storage_service,
)


@pytest.mark.unit
class TestStorageServiceDecomposition:
    """Verifies subpackage architecture, line limits, and service resolvers."""

    def test_submodule_line_counts(self) -> None:
        """Rule 11: All decomposed submodules in storage must be <= 200 lines."""
        storage_dir = Path(__file__).parent.parent / "src" / "harness" / "services" / "storage"
        assert storage_dir.exists() and storage_dir.is_dir()

        py_files = list(storage_dir.glob("*.py"))
        assert len(py_files) >= 7

        for py_file in py_files:
            line_count = len(py_file.read_text(encoding="utf-8").splitlines())
            assert line_count <= 200, f"{py_file.name} has {line_count} lines (> 200 limit)"

    def test_direct_and_submodule_imports(self) -> None:
        """Verify all symbols can be imported from root package and submodules."""
        from harness.services.storage.isnad import IsnadAuditMixin as IAM
        from harness.services.storage.models import (
            IsnadLineageBlock as ILB,
            IsnadLineageNode as ILN,
            KnowledgeItemRecord as KIR,
        )
        from harness.services.storage.plugin import (
            StoragePlugin as SP,
            plugin as p_singleton,
        )
        from harness.services.storage.protocols import (
            KNOWLEDGE_VAULT_KEY as KVK,
            STORAGE_SERVICE_KEY as SSK,
            StorageService as SS,
        )
        from harness.services.storage.resolvers import (
            resolve_knowledge_vault as rkv,
            resolve_storage_service as rss,
        )
        from harness.services.storage.sqlite import SQLiteStorageService as SSS
        from harness.services.storage.vault_operations import KnowledgeVaultMixin as KVM

        assert SS is StorageService
        assert SSS is SQLiteStorageService
        assert SP is StoragePlugin
        assert p_singleton is plugin
        assert SSK is STORAGE_SERVICE_KEY
        assert KVK is KNOWLEDGE_VAULT_KEY
        assert ILN is IsnadLineageNode
        assert ILB is IsnadLineageBlock
        assert KIR is KnowledgeItemRecord
        assert IAM is IsnadAuditMixin
        assert KVM is KnowledgeVaultMixin
        assert rss is resolve_storage_service
        assert rkv is resolve_knowledge_vault

    def test_plugin_module_singleton_and_keys(self) -> None:
        """Rule 45: Plugin singleton exported and declares typed service keys."""
        assert isinstance(plugin, StoragePlugin)
        assert STORAGE_SERVICE_KEY in plugin.provides
        assert KNOWLEDGE_VAULT_KEY in plugin.provides
        assert plugin.trusted is True

    def test_single_seam_service_resolvers(self) -> None:
        """Rule 58: Single-seam resolver checks IoC container before fallback."""
        ctx = ServiceContext()
        custom_storage = SQLiteStorageService(":memory:")
        ctx.provide(STORAGE_SERVICE_KEY, custom_storage)

        resolved_from_ctx = resolve_storage_service(ctx)
        assert resolved_from_ctx is custom_storage

        resolved_kv = resolve_knowledge_vault(ctx)
        assert resolved_kv is custom_storage

        # Fallback when empty context
        empty_ctx = ServiceContext()
        fallback_svc = resolve_storage_service(empty_ctx)
        assert isinstance(fallback_svc, SQLiteStorageService)
        assert fallback_svc is not custom_storage

    @pytest.mark.asyncio
    async def test_knowledge_vault_operations_and_isnad_verification(self, tmp_path: Path) -> None:
        """Rule 40 & Rule 41: Knowledge vault dual-file persistence and isnad integrity."""
        storage = SQLiteStorageService(":memory:")

        # Create dummy source file for provenance
        source_file = tmp_path / "test_engine.py"
        source_file.write_text("def test_core(): pass\n", encoding="utf-8")
        file_hash = storage.compute_sha256(source_file.read_bytes())

        item = KnowledgeItemRecord(
            id="ki_test_001",
            title="Decomposed Storage Invariant",
            source_target=str(source_file),
            detected_format="python_source",
            isnad=IsnadLineageBlock(
                decision_id="dec_001",
                claims=[{
                    "assertion": "Storage engine operates in memory",
                    "lineage": [{
                        "uri": f"file:///{source_file.name}",
                        "sha256_hash": file_hash,
                        "verified": True,
                    }],
                }],
            ),
            tags=["storage", "architecture"],
            summary="Storage engine decomposed into 7 single-responsibility modules.",
        )

        await storage.save_knowledge_item(item)
        fetched = await storage.get_knowledge_item("ki_test_001")
        assert fetched is not None
        assert fetched.id == item.id
        assert fetched.title == item.title

        # Query items
        tagged = await storage.query_knowledge(query="single-responsibility", tag="storage")
        assert len(tagged) == 1
        assert tagged[0].id == "ki_test_001"

        # Verify Isnad integrity
        verification = await storage.verify_isnad_integrity("ki_test_001", base_dir=tmp_path)
        assert verification["status"] == "ok"
        assert verification["integrity_verified"] is True
        assert len(verification["claims_audited"]) == 1

        # Export to dual-file directory vault (Rule 40)
        vault_dir = tmp_path / ".harness" / "knowledge"
        exported_count = await storage.export_knowledge_vault(vault_dir)
        assert exported_count == 1

        ki_dir = vault_dir / "ki_test_001"
        assert ki_dir.is_dir()
        assert (ki_dir / "metadata.json").exists()
        assert (ki_dir / "summary.md").exists()

        # Re-sync from disk
        fresh_storage = SQLiteStorageService(":memory:")
        synced_count = await fresh_storage.sync_knowledge_vault(vault_dir)
        assert synced_count == 1
        synced_item = await fresh_storage.get_knowledge_item("ki_test_001")
        assert synced_item is not None
        assert synced_item.title == item.title
