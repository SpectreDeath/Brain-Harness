"""Knowledge Vault operations mixin for Knowledge Item persistence, sync, and querying."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import structlog

from harness.services.storage.isnad import IsnadAuditMixin
from harness.services.storage.models import IsnadLineageBlock, KnowledgeItemRecord
from harness.services.storage.vault_retrieval import KnowledgeRetrievalMixin

logger = structlog.get_logger()


class KnowledgeVaultMixin(KnowledgeRetrievalMixin, IsnadAuditMixin):
    """Provides high-level Knowledge Item and Isnad provenance methods over key-value storage."""

    async def get(self, key: str) -> Any | None:
        raise NotImplementedError

    async def set(self, key: str, value: Any) -> None:
        raise NotImplementedError

    async def get_all(self, prefix: str = "") -> dict[str, Any]:
        raise NotImplementedError

    async def save_knowledge_item(self, item: KnowledgeItemRecord) -> None:
        """Save a Knowledge Item record under the canonical knowledge prefix."""
        payload = item.model_dump()
        await self.set(f"ki:{item.id}", payload)

    async def get_knowledge_item(self, ki_id: str) -> KnowledgeItemRecord | None:
        """Retrieve a Knowledge Item by its ID."""
        raw = await self.get(f"ki:{ki_id}")
        if raw is None:
            return None
        return KnowledgeItemRecord.model_validate(raw)

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
        """Scan on-disk dual-file knowledge vault (.harness/knowledge/) and sync to storage."""
        root = Path(vault_dir).resolve()
        if not root.exists() or not root.is_dir():
            return 0

        synced_count = 0
        for ki_dir in root.iterdir():
            if not ki_dir.is_dir():
                continue
            meta_file = ki_dir / "metadata.json"
            if not meta_file.exists():
                continue
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                summary_file = ki_dir / "summary.md"
                summary_text = ""
                if summary_file.exists():
                    summary_text = summary_file.read_text(encoding="utf-8")

                if "summary" not in meta or not meta["summary"]:
                    meta["summary"] = summary_text

                ki = KnowledgeItemRecord(
                    id=meta.get("id", ki_dir.name),
                    title=meta.get("title", ki_dir.name),
                    source_target=meta.get("source_target", meta.get("source_brain", "")),
                    detected_format=meta.get("detected_format", "raw_docs"),
                    isnad=meta.get("isnad", {}),
                    tags=meta.get("tags", []),
                    category=meta.get("category", "general"),
                    retrieval_count=int(meta.get("retrieval_count", 0)),
                    success_count=int(meta.get("success_count", 0)),
                    last_retrieved_at=meta.get("last_retrieved_at"),
                    status=meta.get("status", "ACTIVE"),
                    summary=meta.get("summary", summary_text),
                )
                await self.save_knowledge_item(ki)
                synced_count += 1
            except Exception as e:
                logger.warning("Failed to sync knowledge item from disk", dir=str(ki_dir), error=str(e))

        return synced_count

    async def export_knowledge_vault(self, vault_dir: Path | str = ".harness/knowledge") -> int:
        """Export all stored knowledge items to the on-disk dual-file vault."""
        root = Path(vault_dir).resolve()
        root.mkdir(parents=True, exist_ok=True)
        items = await self.list_knowledge_items()
        exported = 0

        for item in items:
            ki_dir = root / item.id
            ki_dir.mkdir(parents=True, exist_ok=True)
            meta_file = ki_dir / "metadata.json"
            summary_file = ki_dir / "summary.md"

            meta_data = {
                "id": item.id,
                "title": item.title,
                "source_target": item.source_target,
                "detected_format": item.detected_format,
                "isnad": item.isnad.model_dump() if isinstance(item.isnad, IsnadLineageBlock) else item.isnad,
                "tags": item.tags,
                "category": item.category,
                "retrieval_count": item.retrieval_count,
                "success_count": item.success_count,
                "last_retrieved_at": item.last_retrieved_at,
                "status": item.status,
                "context": getattr(item, "context", f"Knowledge item {item.id}"),
                "distilled_learning": item.summary.split("\n")[0] if item.summary else item.title,
            }
            meta_file.write_text(json.dumps(meta_data, indent=2), encoding="utf-8")

            if item.summary:
                summary_file.write_text(item.summary, encoding="utf-8")
            elif not summary_file.exists():
                summary_file.write_text(f"# {item.title}\n\n{item.summary or item.title}\n", encoding="utf-8")

            exported += 1

        return exported

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
                item_status = "UNKNOWN"
                if isinstance(item.isnad, IsnadLineageBlock):
                    item_status = item.isnad.status
                elif isinstance(item.isnad, dict):
                    item_status = item.isnad.get("status", "VERIFIED" if item.isnad.get("verified") else "UNKNOWN")
                if item_status.upper() != status.upper():
                    continue

            if q_lower:
                searchable = f"{item.title} {item.summary} {' '.join(item.tags)} {item.source_target}".lower()
                if q_lower not in searchable:
                    continue

            filtered.append(item)

        return filtered
