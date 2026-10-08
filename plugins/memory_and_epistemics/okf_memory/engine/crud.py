"""OKF concept CRUD operations, bookkeeping synchronization, and relation management."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .utils import (
    ALLOWED_TYPES,
    _ensure_within_root,
    _normalize_path,
    _serialize_concept,
    load_bundle_concepts,
)


def execute_show(root: Path, concept_id: str) -> dict[str, Any] | None:
    """Retrieve full concept record by id."""
    concepts = load_bundle_concepts(root)
    if concept_id not in concepts:
        return None

    data, body, _file_path = concepts[concept_id]
    return {
        "id": concept_id,
        "title": data.get("title", ""),
        "type": data.get("type", "concept"),
        "description": data.get("description", ""),
        "body": body,
        "governance": data.get("governance") or [],
        "code_refs": data.get("code_refs") or [],
        "generated": data.get("generated") or {},
        "verified": data.get("verified") or {},
        "sources": data.get("sources") or [],
        "extra": {
            k: v
            for k, v in data.items()
            if k not in {
                "id",
                "title",
                "type",
                "description",
                "governance",
                "code_refs",
                "generated",
                "verified",
                "sources",
            }
        },
    }


def sync_index_and_log(
    root: Path,
    action: str,
    concept_id: str,
    actor: str = "agent:brain-harness",
    details: str = "",
) -> None:
    """Auto-update parent index.md table and append audit entry to log.md."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # 1. Update log.md
    log_file = root / "log.md"
    log_entry = f"| {now_utc} | {action.upper()} | {concept_id} | {actor} | {details} |\n"
    if not log_file.exists():
        header = (
            "# Knowledge Audit Log\n\n"
            "| Timestamp (UTC) | Action | Concept ID | Actor | Details |\n"
            "|---|---|---|---|---|\n"
        )
        log_file.write_text(header + log_entry, encoding="utf-8")
    else:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

    # 2. Update index.md
    index_file = root / "index.md"
    concepts = load_bundle_concepts(root)
    rows = [
        "# Knowledge Index\n",
        "This table is automatically maintained. Do not edit manually.\n",
        "| ID | Type | Title | Description |",
        "|---|---|---|---|",
    ]
    for cid, (data, _, _) in sorted(concepts.items()):
        title = str(data.get("title", "")).replace("|", "\\|").strip()
        ctype = str(data.get("type", "concept")).replace("|", "\\|").strip()
        desc = str(data.get("description", "")).replace("|", "\\|").replace("\n", " ").strip()
        rows.append(f"| [{cid}]({cid}.md) | {ctype} | {title} | {desc} |")
    rows.append("")
    index_file.write_text("\n".join(rows), encoding="utf-8")


def execute_create(
    root: Path,
    concept_id: str,
    title: str,
    concept_type: str,
    description: str,
    body: str = "",
    governance: list[str] | None = None,
    code_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new concept document with frontmatter sanitization and auto-sync."""
    cid = concept_id.strip()
    if not cid:
        raise ValueError("Concept ID cannot be empty")

    target_file = root / f"{cid}.md"
    _ensure_within_root(root, target_file)

    if target_file.exists():
        raise FileExistsError(f"Concept '{cid}' already exists at {target_file}")

    # Sanitize scalar fields to eliminate unescaped newlines
    clean_title = title.replace("\r", "").replace("\n", " ").strip()
    clean_type = concept_type.replace("\r", "").replace("\n", "").strip().lower()
    clean_desc = description.replace("\r", "").replace("\n", " ").strip()

    now_iso = datetime.now(timezone.utc).isoformat()
    data: dict[str, Any] = {
        "id": cid,
        "title": clean_title,
        "type": clean_type if clean_type in ALLOWED_TYPES else "concept",
        "description": clean_desc,
        "governance": [str(g).strip() for g in (governance or []) if str(g).strip()],
        "code_refs": [_normalize_path(c) for c in (code_refs or []) if str(c).strip()],
        "generated": {
            "by": "agent:brain-harness",
            "at": now_iso,
        },
    }

    full_content = _serialize_concept(data, body)
    target_file.write_text(full_content, encoding="utf-8")

    # Auto-sync index and audit log (Rule 5 / UpdateParentIndex)
    sync_index_and_log(
        root=root,
        action="CREATE",
        concept_id=cid,
        details=f"Created concept: {clean_title}",
    )

    return execute_show(root, cid) or data


def execute_update(
    root: Path,
    concept_id: str,
    title: str | None = None,
    description: str | None = None,
    body: str | None = None,
    governance: list[str] | None = None,
    code_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Update an existing concept file and sync bookkeeping."""
    concepts = load_bundle_concepts(root)
    cid = concept_id.strip()

    if cid not in concepts:
        raise FileNotFoundError(f"Concept '{cid}' not found in bundle at {root}")

    data, old_body, target_file = concepts[cid]
    _ensure_within_root(root, target_file)

    if title is not None:
        data["title"] = title.replace("\r", "").replace("\n", " ").strip()
    if description is not None:
        data["description"] = description.replace("\r", "").replace("\n", " ").strip()
    if governance is not None:
        data["governance"] = [str(g).strip() for g in governance if str(g).strip()]
    if code_refs is not None:
        data["code_refs"] = [_normalize_path(c) for c in code_refs if str(c).strip()]

    new_body = body if body is not None else old_body
    full_content = _serialize_concept(data, new_body)
    target_file.write_text(full_content, encoding="utf-8")

    sync_index_and_log(
        root=root,
        action="UPDATE",
        concept_id=cid,
        details="Updated concept properties",
    )

    return execute_show(root, cid) or data


def execute_relate(
    root: Path,
    source_id: str,
    target_id: str,
    description: str = "",
) -> dict[str, Any]:
    """Bidirectionally relate two concepts in frontmatter."""
    concepts = load_bundle_concepts(root)

    src_id = source_id.strip()
    tgt_id = target_id.strip()

    if src_id not in concepts:
        raise FileNotFoundError(f"Source concept '{src_id}' not found")
    if tgt_id not in concepts:
        raise FileNotFoundError(f"Target concept '{tgt_id}' not found")

    src_data, src_body, src_file = concepts[src_id]
    tgt_data, tgt_body, tgt_file = concepts[tgt_id]

    _ensure_within_root(root, src_file)
    _ensure_within_root(root, tgt_file)

    # Update source relations
    src_relations = src_data.get("relations") or []
    if not any(r.get("target") == tgt_id for r in src_relations if isinstance(r, dict)):
        src_relations.append({"target": tgt_id, "description": description.strip()})
        src_data["relations"] = src_relations
        src_file.write_text(_serialize_concept(src_data, src_body), encoding="utf-8")

    # Update target relations reciprocally
    tgt_relations = tgt_data.get("relations") or []
    if not any(r.get("target") == src_id for r in tgt_relations if isinstance(r, dict)):
        tgt_relations.append({"target": src_id, "description": description.strip()})
        tgt_data["relations"] = tgt_relations
        tgt_file.write_text(_serialize_concept(tgt_data, tgt_body), encoding="utf-8")

    sync_index_and_log(
        root=root,
        action="RELATE",
        concept_id=src_id,
        details=f"Linked to {tgt_id}: {description}",
    )

    return {
        "status": "ok",
        "source": src_id,
        "target": tgt_id,
        "description": description,
    }
