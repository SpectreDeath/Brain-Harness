"""Knowledge Vault operations mixin for Knowledge Item persistence, sync, and querying."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

from harness.services.storage.isnad import IsnadAuditMixin
from harness.services.storage.models import IsnadLineageBlock, KnowledgeEdge, KnowledgeItemRecord
from harness.services.storage.vault_contradiction import ContradictionDetector, ContradictionReviewItem
from harness.services.storage.vault_graph import KnowledgeGraphQueryService
from harness.services.storage.vault_retrieval import KnowledgeRetrievalMixin
from harness.services.storage.vault_taxonomy import normalize_category

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
        payload = item.model_dump()
        await self.set(f"ki:{item.id}", payload)
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

    async def sync_knowledge_vault(self, vault_dir: Path | str = ".harness/knowledge") -> int:
        """Scan on-disk dual-file knowledge vault and sync to storage, unifying metadata eras."""
        root = Path(vault_dir).resolve()
        if not root.exists() or not root.is_dir():
            return 0

        synced_count = 0
        graph_service = KnowledgeGraphQueryService()
        for ki_dir in root.iterdir():
            if not ki_dir.is_dir():
                continue
            meta_file = ki_dir / "metadata.json"
            if not meta_file.exists():
                continue
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                summary_file = ki_dir / "summary.md"
                summary_text = summary_file.read_text(encoding="utf-8") if summary_file.exists() else ""
                edges = [KnowledgeEdge.model_validate(e) for e in meta.get("edges", [])]

                ki = KnowledgeItemRecord(
                    schema_version=meta.get("schema_version", "1.0.0"),
                    id=meta.get("id", ki_dir.name),
                    title=meta.get("title", ki_dir.name),
                    source_target=meta.get("source_target") or meta.get("source_brain", ""),
                    detected_format=meta.get("detected_format", "raw_docs"),
                    isnad=meta.get("isnad", {}),
                    tags=meta.get("tags", []),
                    category=normalize_category(meta.get("category")),
                    edges=edges,
                    anchors=meta.get("anchors", {}),
                    author=meta.get("author"),
                    retrieval_count=int(meta.get("retrieval_count", 0)),
                    success_count=int(meta.get("success_count", 0)),
                    last_retrieved_at=meta.get("last_retrieved_at"),
                    status=meta.get("status", "ACTIVE"),
                    superseded_by=meta.get("superseded_by"),
                    summary=meta.get("summary") or summary_text,
                )
                if not ki.edges:
                    graph_service.backfill_edges_mechanically([ki])
                await self.save_knowledge_item(ki)
                synced_count += 1
            except Exception as e:
                logger.warning("Failed to sync knowledge item from disk", dir=str(ki_dir), error=str(e))
        return synced_count

    async def export_single_item(self, item: KnowledgeItemRecord, vault_dir: Path | str = ".harness/knowledge") -> None:
        """Export a single Knowledge Item to canonical dual-file format on disk (Rule 40)."""
        root = Path(vault_dir).resolve()
        ki_dir = root / item.id
        ki_dir.mkdir(parents=True, exist_ok=True)
        meta_file = ki_dir / "metadata.json"
        summary_file = ki_dir / "summary.md"

        meta_data = {
            "schema_version": item.schema_version,
            "id": item.id,
            "title": item.title,
            "category": item.category,
            "source_target": item.source_target,
            "detected_format": item.detected_format,
            "tags": item.tags,
            "anchors": item.anchors,
            "edges": [e.model_dump() for e in item.edges],
            "isnad": item.isnad.model_dump() if isinstance(item.isnad, IsnadLineageBlock) else item.isnad,
            "retrieval_count": item.retrieval_count,
            "success_count": item.success_count,
            "last_retrieved_at": item.last_retrieved_at,
            "status": item.status,
            "superseded_by": item.superseded_by,
            "author": item.author,
            "created_at": item.created_at,
            "distilled_learning": item.summary.split("\n")[0] if item.summary else item.title,
        }
        meta_file.write_text(json.dumps(meta_data, indent=2), encoding="utf-8")
        if item.summary:
            summary_file.write_text(item.summary, encoding="utf-8")
        elif not summary_file.exists():
            summary_file.write_text(f"# {item.title}\n\n{item.title}\n", encoding="utf-8")

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
        self,
        query: str = "",
        tag: str | None = None,
        status: str | None = None,
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
