"""Knowledge Vault operations mixin for Knowledge Item persistence, sync, and querying."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

import structlog

from harness.services.storage.isnad import IsnadAuditMixin
from harness.services.storage.models import IsnadLineageBlock, KnowledgeEdge, KnowledgeItemRecord
from harness.services.storage.vault_contradiction import ContradictionDetector, ContradictionReviewItem
from harness.services.storage.vault_export import _CANONICAL_KI_KEYS, export_single_item_to_disk
from harness.services.storage.vault_graph import KnowledgeGraphQueryService
from harness.services.storage.vault_retrieval import KnowledgeRetrievalMixin
from harness.services.storage.vault_taxonomy import (
    normalize_category, normalize_isnad, resolve_created_at,
    resolve_created_at_with_source, resolve_source_target,
)

logger = structlog.get_logger()


class KnowledgeVaultMixin(KnowledgeRetrievalMixin, IsnadAuditMixin):
    """Provides high-level Knowledge Item and Isnad provenance methods over key-value storage."""

    async def get(self, key: str) -> Any | None:
        raise NotImplementedError

    async def set(self, key: str, value: Any) -> None:
        raise NotImplementedError

    async def get_all(self, prefix: str = "") -> dict[str, Any]:
        raise NotImplementedError

    async def save_knowledge_item(self, item: KnowledgeItemRecord, vault_dir: Path | str | None = None) -> None:
        """Save a Knowledge Item record under the canonical knowledge prefix and optionally flush to disk."""
        await self.set(f"ki:{item.id}", item.model_dump())
        if vault_dir:
            await self.export_single_item(item, vault_dir=vault_dir)

    async def get_knowledge_item(self, ki_id: str) -> KnowledgeItemRecord | None:
        """Retrieve a Knowledge Item by its ID."""
        raw = await self.get(f"ki:{ki_id}")
        return KnowledgeItemRecord.model_validate(raw) if raw is not None else None

    async def list_knowledge_items(self, tag: str | None = None) -> list[KnowledgeItemRecord]:
        """List all Knowledge Items, optionally filtered by tag."""
        records = await self.get_all(prefix="ki:")
        items: list[KnowledgeItemRecord] = []
        for val in records.values():
            try:
                ki = KnowledgeItemRecord.model_validate(val)
                if tag is None or tag in ki.tags:
                    items.append(ki)
            except Exception as e:
                logger.warning("Failed to validate knowledge item", error=str(e))
        return items

    def get_last_skipped_items(self) -> list[tuple[str, str]]:
        return getattr(self, "_last_skipped_items", [])

    async def sync_knowledge_vault(
        self, vault_dir: Path | str = ".harness/knowledge", strict: bool = False,
    ) -> int:
        """Scan on-disk dual-file knowledge vault and sync to storage, unifying metadata eras."""
        root = Path(vault_dir).resolve()
        if not root.exists() or not root.is_dir():
            return 0

        synced_items: list[KnowledgeItemRecord] = []
        skipped_items: list[tuple[str, str]] = []
        graph_service = KnowledgeGraphQueryService()

        for ki_dir in root.iterdir():
            if not ki_dir.is_dir():
                continue
            meta_file = ki_dir / "metadata.json"
            if not meta_file.exists():
                skipped_items.append((ki_dir.name, "Missing metadata.json"))
                logger.warning("Vault directory missing metadata.json", dir=str(ki_dir))
                continue
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                summary_file = ki_dir / "summary.md"
                summary_text = summary_file.read_text(encoding="utf-8") if summary_file.exists() else ""
                edges = [KnowledgeEdge.model_validate(e) for e in meta.get("edges", [])]

                ki_id = meta.get("id") or meta.get("ki_id") or ki_dir.name
                source_target = resolve_source_target(meta)
                created_at, date_source = resolve_created_at_with_source(meta, ki_dir)
                isnad = normalize_isnad(meta)

                extra_kwargs = {k: v for k, v in meta.items() if k not in _CANONICAL_KI_KEYS}
                extra_kwargs["_date_source"] = date_source
                if "summary" in meta:
                    extra_kwargs["_metadata_summary"] = meta["summary"]

                ki = KnowledgeItemRecord(
                    schema_version=meta.get("schema_version", "1.0.0"),
                    id=ki_id, title=meta.get("title", ki_id), source_target=source_target,
                    detected_format=meta.get("detected_format", "raw_docs"),
                    isnad=isnad, tags=meta.get("tags", []),
                    category=normalize_category(meta.get("category")),
                    edges=edges, anchors=meta.get("anchors", {}), author=meta.get("author"),
                    retrieval_count=int(meta.get("retrieval_count", 0)),
                    success_count=int(meta.get("success_count", 0)),
                    last_retrieved_at=meta.get("last_retrieved_at"),
                    status=meta.get("status", "ACTIVE"), superseded_by=meta.get("superseded_by"),
                    summary=summary_text or meta.get("summary", ""), created_at=created_at,
                    **extra_kwargs,
                )
                synced_items.append(ki)
            except Exception as e:
                skipped_items.append((ki_dir.name, str(e)))
                logger.warning("Failed to sync knowledge item from disk", dir=str(ki_dir), error=str(e))

        self._last_skipped_items = skipped_items
        if strict and skipped_items:
            raise ValueError(
                f"Sync failed in strict mode with {len(skipped_items)} skipped item(s): "
                f"{', '.join(f'{d} ({err})' for d, err in skipped_items[:5])}"
            )

        items_needing_backfill = [k for k in synced_items if not k.edges]
        if items_needing_backfill:
            graph_service.backfill_edges_mechanically(synced_items, vault_dir=root)
            for ki in items_needing_backfill:
                if ki.edges and (root / ki.id / "metadata.json").exists():
                    try:
                        ki_meta_file = root / ki.id / "metadata.json"
                        m_data = json.loads(ki_meta_file.read_text(encoding="utf-8"))
                        m_data["edges"] = [e.model_dump() for e in ki.edges]
                        ki_meta_file.write_text(json.dumps(m_data, indent=2) + "\n", encoding="utf-8")
                    except Exception as ex:
                        logger.warning("Failed writing backfilled edges to disk", ki_id=ki.id, error=str(ex))

        for ki in synced_items:
            await self.save_knowledge_item(ki)

        synced_ids = {ki.id for ki in synced_items}
        if hasattr(self, "list_knowledge_items"):
            try:
                for old_item in await self.list_knowledge_items():
                    if old_item.id not in synced_ids and hasattr(self, "delete_knowledge_item"):
                        await self.delete_knowledge_item(old_item.id)
            except Exception as ex:
                logger.debug("Failed pruning stale KV items", error=str(ex))

        if hasattr(self, "_ensure_connection"):
            from harness.services.storage.vault_derivation import derive_knowledge_graph
            from harness.services.storage.vault_sqlite_graph import sync_ki_edges

            graph = derive_knowledge_graph(synced_items)
            sync_ki_edges(self._ensure_connection(), graph)

        return len(synced_items)

    async def export_single_item(self, item: KnowledgeItemRecord, vault_dir: Path | str = ".harness/knowledge") -> None:
        """Export a single Knowledge Item to canonical dual-file format on disk (Rule 40)."""
        await export_single_item_to_disk(item, vault_dir=vault_dir)

    async def export_knowledge_vault(self, vault_dir: Path | str = ".harness/knowledge") -> int:
        """Export all stored knowledge items to the on-disk dual-file vault."""
        items = await self.list_knowledge_items()
        for item in items:
            await self.export_single_item(item, vault_dir=vault_dir)
        return len(items)

    async def audit_contradictions(self) -> list[ContradictionReviewItem]:
        """Audit all stored Knowledge Items for contradictions, supersessions, and antinomies."""
        items = await self.list_knowledge_items()
        return ContradictionDetector().detect_contradictions(items)

    async def query_knowledge(
        self, query: str = "", tag: str | None = None, status: str | None = None,
    ) -> list[KnowledgeItemRecord]:
        """Query knowledge items by search term, tag, and isnad status."""
        items = await self.list_knowledge_items(tag=tag)
        if not query and not status:
            return items
        q_lower = query.lower().strip()
        filtered: list[KnowledgeItemRecord] = []
        for item in items:
            if status:
                st = item.isnad.status if isinstance(item.isnad, IsnadLineageBlock) else item.isnad.get("status", "UNKNOWN") if isinstance(item.isnad, dict) else "UNKNOWN"
                if st.upper() != status.upper():
                    continue
            if q_lower:
                searchable = f"{item.title} {item.summary} {' '.join(item.tags)} {item.source_target}".lower()
                if q_lower not in searchable:
                    continue
            filtered.append(item)
        return filtered
