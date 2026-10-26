"""Knowledge Vault retrieval, scoring, prompt formatting, and evidence-based lifecycle tracking."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, cast

import structlog

from harness.services.storage.models import KnowledgeItemRecord

logger = structlog.get_logger()


class KnowledgeRetrievalMixin:
    """Provides semantic matching, bounded prompt injection, and feedback loop tracking."""

    async def list_knowledge_items(self, tag: str | None = None) -> list[KnowledgeItemRecord]:
        raise NotImplementedError

    async def get_knowledge_item(self, ki_id: str) -> KnowledgeItemRecord | None:
        raise NotImplementedError

    async def save_knowledge_item(self, item: KnowledgeItemRecord) -> None:
        raise NotImplementedError

    async def sync_knowledge_vault(self, vault_dir: Path | str = ".harness/knowledge") -> int:
        raise NotImplementedError

    async def retrieve_relevant_knowledge(
        self,
        task: str,
        max_items: int = 3,
        min_score: float = 0.15,
        vault_dir: Path | str = ".harness/knowledge",
    ) -> list[KnowledgeItemRecord]:
        """Retrieve most relevant Knowledge Items from Knowledge Vault for a task."""
        items = await self.list_knowledge_items()
        if not items:
            await self.sync_knowledge_vault(vault_dir)
            items = await self.list_knowledge_items()

        if not items:
            return []

        tokens = set(re.findall(r"[a-zA-Z0-9_-]{3,}", task.lower()))
        stopwords = {
            "the", "and", "for", "with", "from", "that", "this", "into", "over",
            "after", "before", "about", "your", "have", "been", "will", "would",
            "could", "should", "each", "other", "every", "some", "such", "than",
        }
        query_terms = [t for t in tokens if t not in stopwords]
        if not query_terms:
            return []

        scored_items: list[tuple[float, KnowledgeItemRecord]] = []
        for item in items:
            if item.status == "ARCHIVED":
                continue

            tag_score = sum(
                4.0 if q == tag.lower() else (2.0 if q in tag.lower() else 0.0)
                for tag in item.tags
                for q in query_terms
            )
            cat_lower = (item.category or "").lower()
            cat_score = sum(
                3.0 if q == cat_lower else (1.5 if q in cat_lower else 0.0)
                for q in query_terms
            )
            title_lower = item.title.lower()
            title_score = sum(1.5 for q in query_terms if q in title_lower)
            summary_lower = (item.summary or "").lower()[:300]
            summary_score = sum(0.5 for q in query_terms if q in summary_lower)

            base_score = tag_score + cat_score + title_score + summary_score
            if base_score <= 0.0:
                continue

            status_mult = 1.25 if item.status == "PROMOTED" else (0.5 if item.status == "DEMOTED" else 1.0)
            utility_boost = (item.success_count / item.retrieval_count * 1.5) if item.retrieval_count > 0 else 0.0

            total_score = (base_score * status_mult) + utility_boost
            if total_score >= min_score:
                scored_items.append((total_score, item))

        scored_items.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored_items[:max_items]]

    def retrieve_relevant_knowledge_sync(
        self,
        task: str,
        max_items: int = 3,
        min_score: float = 0.15,
        vault_dir: Path | str = ".harness/knowledge",
    ) -> list[KnowledgeItemRecord]:
        from harness.creator.validator.base import _run_coro_sync

        return cast(
            list[KnowledgeItemRecord],
            _run_coro_sync(self.retrieve_relevant_knowledge(task=task, max_items=max_items, min_score=min_score, vault_dir=vault_dir)),
        )

    @staticmethod
    def format_knowledge_prompt_block(items: list[KnowledgeItemRecord], max_chars_per_item: int = 250) -> str:
        if not items:
            return ""
        lines = ["\n\n## Relevant Knowledge Vault Heuristics"]
        for ki in items:
            first_line = (ki.summary or "").strip().split("\n")[0]
            if len(first_line) > max_chars_per_item:
                first_line = first_line[:max_chars_per_item].rstrip() + "..."
            lines.append(f"- [{ki.id}] **{ki.title}**")
            if first_line:
                lines.append(f"  Guideline: {first_line}")
        return "\n".join(lines)

    async def record_knowledge_retrieval(self, ki_ids: list[str], vault_dir: Path | str = ".harness/knowledge") -> None:
        if not ki_ids:
            return
        from datetime import datetime, timezone

        now_iso = datetime.now(timezone.utc).isoformat()
        root = Path(vault_dir).resolve()
        for ki_id in ki_ids:
            item = await self.get_knowledge_item(ki_id)
            if item:
                item.retrieval_count += 1
                item.last_retrieved_at = now_iso
                await self.save_knowledge_item(item)
                meta_path = root / ki_id / "metadata.json"
                if meta_path.exists():
                    try:
                        raw = json.loads(meta_path.read_text(encoding="utf-8"))
                        raw["retrieval_count"] = item.retrieval_count
                        raw["last_retrieved_at"] = now_iso
                        meta_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
                    except Exception as e:
                        logger.debug("Failed to update disk metadata", ki_id=ki_id, error=str(e))

    async def record_knowledge_outcome(self, ki_ids: list[str], success: bool, vault_dir: Path | str = ".harness/knowledge") -> None:
        if not ki_ids:
            return
        root = Path(vault_dir).resolve()
        for ki_id in ki_ids:
            item = await self.get_knowledge_item(ki_id)
            if item:
                if success:
                    item.success_count += 1
                await self.save_knowledge_item(item)
                meta_path = root / ki_id / "metadata.json"
                if meta_path.exists():
                    try:
                        raw = json.loads(meta_path.read_text(encoding="utf-8"))
                        raw["success_count"] = item.success_count
                        meta_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
                    except Exception as e:
                        logger.debug("Failed to update disk outcome", ki_id=ki_id, error=str(e))

    async def evaluate_vault_lifecycle(
        self,
        min_retrievals: int = 5,
        promote_ratio: float = 0.75,
        demote_ratio: float = 0.25,
        vault_dir: Path | str = ".harness/knowledge",
    ) -> dict[str, list[str]]:
        items = await self.list_knowledge_items()
        promoted, demoted, root = [], [], Path(vault_dir).resolve()
        for item in items:
            if item.retrieval_count < min_retrievals:
                continue
            ratio = item.success_count / item.retrieval_count
            new_status = item.status
            if ratio >= promote_ratio and item.status != "PROMOTED":
                new_status = "PROMOTED"
                promoted.append(item.id)
            elif ratio <= demote_ratio and item.status != "DEMOTED":
                new_status = "DEMOTED"
                demoted.append(item.id)
            if new_status != item.status:
                item.status = new_status
                await self.save_knowledge_item(item)
                meta_path = root / item.id / "metadata.json"
                if meta_path.exists():
                    try:
                        raw = json.loads(meta_path.read_text(encoding="utf-8"))
                        raw["status"] = new_status
                        meta_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
                    except Exception as e:
                        logger.debug("Failed to update disk status", ki_id=item.id, error=str(e))
        return {"promoted": promoted, "demoted": demoted}
