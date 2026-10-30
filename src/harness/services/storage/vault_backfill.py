"""Mechanical edge backfilling and link suggestion algorithms (Rule 11, Rule 12)."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Sequence

from harness.services.storage.models import KnowledgeEdge, KnowledgeItemRecord
from harness.services.storage.vault_taxonomy import get_taxonomy_domain


def propose_links(
    ki: KnowledgeItemRecord,
    existing: Sequence[KnowledgeItemRecord],
    *,
    max_tag_freq: float = 0.15,
) -> list[KnowledgeEdge]:
    """Propose candidate edges for a newly created or updated Knowledge Item."""
    proposed: list[KnowledgeEdge] = []
    domain = get_taxonomy_domain(ki.category)
    tags = set(ki.tags)

    if ki.source_target and ("src/" in ki.source_target or "plugins/" in ki.source_target):
        proposed.append(KnowledgeEdge(type="references_code", target=ki.source_target, target_kind="path", derived=True, confidence=0.95))

    target_skill = ki.anchors.get("target_skill")
    if target_skill:
        proposed.append(KnowledgeEdge(type="became_skill", target=str(target_skill), target_kind="skill", derived=False, confidence=1.0))

    target_plugin = ki.anchors.get("plugin") or ki.anchors.get("service_key")
    if target_plugin:
        proposed.append(KnowledgeEdge(type="became_plugin", target=str(target_plugin), target_kind="plugin", derived=False, confidence=1.0))

    total = len(existing)
    tag_counts = Counter(t for other in existing for t in set(other.tags))
    mega_tags = {t for t, c in tag_counts.items() if total >= 10 and (c / total) > max_tag_freq}

    for other in existing:
        if other.id == ki.id:
            continue
        if other.superseded_by == ki.id:
            proposed.append(KnowledgeEdge(type="supersedes", target=other.id, target_kind="ki", derived=False, confidence=1.0))
        elif domain != "general" and domain == get_taxonomy_domain(other.category):
            shared = (tags & set(other.tags)) - mega_tags
            if len(shared) >= 2:
                proposed.append(KnowledgeEdge(type="same_domain", target=other.id, target_kind="ki", derived=True, confidence=0.80))
    return proposed


def backfill_edges_mechanically(
    items: Sequence[KnowledgeItemRecord],
    vault_dir: Path | str = ".harness/knowledge",
    max_tag_freq: float = 0.15,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Mechanically backfill references_code, became_skill, became_plugin, supersedes, and same_domain edges."""
    vault_root = Path(vault_dir).resolve() if vault_dir else None
    id_map = {item.id: item for item in items}
    total = len(items)
    tag_counts = Counter(t for ki in items for t in set(ki.tags))
    mega_tags = {t for t, c in tag_counts.items() if total >= 10 and (c / total) > max_tag_freq}

    added_by_type: Counter[str] = Counter()
    total_added = 0
    items_updated_set: set[str] = set()

    def _maybe_add(ki: KnowledgeItemRecord, edge_type: str, target: str, target_kind: str, derived: bool, confidence: float) -> bool:
        nonlocal total_added
        if any(e.type == edge_type and e.target == target for e in ki.edges):
            return False
        total_added += 1
        added_by_type[edge_type] += 1
        items_updated_set.add(ki.id)
        if not dry_run:
            ki.add_edge(edge_type, target, target_kind=target_kind, derived=derived, confidence=confidence)
        return True

    for ki in items:
        if ki.source_target and ("src/" in ki.source_target or "plugins/" in ki.source_target):
            _maybe_add(ki, "references_code", ki.source_target, "path", derived=True, confidence=0.95)

        target_skill = ki.anchors.get("target_skill")
        if target_skill:
            _maybe_add(ki, "became_skill", str(target_skill), "skill", derived=False, confidence=1.0)

        for t in ki.tags:
            if t.startswith("skill:"):
                _maybe_add(ki, "became_skill", t[6:], "skill", derived=False, confidence=1.0)
            elif t.startswith("plugin:"):
                _maybe_add(ki, "became_plugin", t[7:], "plugin", derived=False, confidence=1.0)

        if ki.superseded_by and ki.superseded_by in id_map:
            rep = id_map[ki.superseded_by]
            _maybe_add(rep, "supersedes", ki.id, "ki", derived=False, confidence=1.0)

        if vault_root:
            meta_path = vault_root / ki.id / "metadata.json"
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                    for ref in meta.get("references", []):
                        ref_path = ref.get("path") if isinstance(ref, dict) else str(ref)
                        if not ref_path:
                            continue
                        if ".agents/skills/" in ref_path or ref_path.startswith("skills/"):
                            parts = ref_path.replace("\\", "/").split("/")
                            if "skills" in parts:
                                s_idx = parts.index("skills")
                                if s_idx + 1 < len(parts):
                                    _maybe_add(ki, "became_skill", parts[s_idx + 1], "skill", derived=False, confidence=1.0)
                        elif "src/" in ref_path or "plugins/" in ref_path or ref_path.endswith(".py"):
                            _maybe_add(ki, "references_code", ref_path, "path", derived=True, confidence=0.95)
                    for plug in meta.get("plugins_scaffolded", []):
                        _maybe_add(ki, "became_plugin", str(plug), "plugin", derived=False, confidence=1.0)
                except Exception:
                    pass

    dom_map: dict[str, list[KnowledgeItemRecord]] = {}
    for ki in items:
        d = get_taxonomy_domain(ki.category)
        if d != "general":
            dom_map.setdefault(d, []).append(ki)

    for dom, group in dom_map.items():
        for i in range(len(group)):
            ki_a = group[i]
            tags_a = set(ki_a.tags) - mega_tags
            for j in range(i + 1, len(group)):
                ki_b = group[j]
                tags_b = set(ki_b.tags) - mega_tags
                if len(tags_a & tags_b) >= 2:
                    _maybe_add(ki_a, "same_domain", ki_b.id, "ki", derived=True, confidence=0.80)

    return {
        "total_added": total_added,
        "added_by_type": dict(added_by_type),
        "items_updated_count": len(items_updated_set),
        "dry_run": dry_run,
    }
