"""Knowledge Vault export utilities for canonical dual-file formatting on disk (Rule 40)."""

from __future__ import annotations

import json
from pathlib import Path
import structlog

from harness.services.storage.models import IsnadLineageBlock, KnowledgeItemRecord

logger = structlog.get_logger(__name__)

_CANONICAL_KI_KEYS: frozenset[str] = frozenset({
    "schema_version",
    "id",
    "ki_id",
    "title",
    "source_target",
    "detected_format",
    "isnad",
    "claims",
    "isnad_claims",
    "tags",
    "category",
    "edges",
    "anchors",
    "author",
    "retrieval_count",
    "success_count",
    "last_retrieved_at",
    "status",
    "superseded_by",
    "summary",
    "created_at",
})


async def export_single_item_to_disk(
    item: KnowledgeItemRecord,
    vault_dir: Path | str = ".harness/knowledge",
) -> None:
    """Export a single Knowledge Item to canonical dual-file format on disk (Rule 40).

    Performs a non-destructive read-modify-write merge if metadata.json exists to preserve
    historical keys (context, provenance, references, source_repo, etc.).
    """
    root = Path(vault_dir).resolve()
    ki_dir = root / item.id
    ki_dir.mkdir(parents=True, exist_ok=True)
    meta_file = ki_dir / "metadata.json"
    summary_file = ki_dir / "summary.md"

    if meta_file.exists():
        try:
            meta_data = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Corrupt metadata.json encountered during export", file=str(meta_file), error=str(e))
            meta_data = {}
    else:
        meta_data = {}

    if item.model_extra:
        for k, v in item.model_extra.items():
            if k == "_metadata_summary":
                meta_data["summary"] = v
                continue
            if k.startswith("_"):
                continue  # Prevent sync-injected keys (_date_source) from polluting export
            if k not in meta_data:
                meta_data[k] = v

    if "_metadata_summary" in meta_data:
        meta_data["summary"] = meta_data.pop("_metadata_summary")

    distilled = meta_data.get("distilled_learning")
    if not distilled:
        distilled = item.summary.split("\n")[0] if item.summary else item.title

    canonical_updates = {
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
        "distilled_learning": distilled,
    }
    meta_data.update(canonical_updates)
    meta_file.write_text(json.dumps(meta_data, indent=2), encoding="utf-8")
    if item.summary:
        summary_file.write_text(item.summary, encoding="utf-8")
    elif not summary_file.exists():
        summary_file.write_text(f"# {item.title}\n\n{item.title}\n", encoding="utf-8")
