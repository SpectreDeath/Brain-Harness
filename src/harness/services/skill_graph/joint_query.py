"""Cross-graph joint query across Knowledge Vault and Skill Knowledge Graph.

Unifies epistemic facts (what the harness knows) with procedural capabilities (how the harness acts).

Architectural Decision Rationale (Track 6):
query_knowledge_and_skills reads directly from canonical dual-file metadata.json (Rule 40)
rather than instantiating SQLiteStorageService or acquiring SQLite connection locks.
This guarantees:
1. Sub-5ms CLI cold-start latency for interactive queries (`harness knowledge joint-query`).
2. Complete zero-lock immunity against worker proactors and concurrent session writers (Rule 22).
3. Direct inspection of declared `became_skill` / `distilled_from` graph edges with semantic domain fallbacks.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from harness.kernel.context import ServiceContext
from harness.commands.skills.routing import route_skills_cmd


def query_knowledge_and_skills(
    topic: str,
    *,
    vault_dir: str = ".harness/knowledge",
    root_path: str = ".",
    limit: int = 5,
    ctx: ServiceContext | None = None,
) -> dict[str, Any]:
    """Execute unified dual-graph query joining Knowledge Vault KIs and Skill Graph nodes."""
    vault_root = Path(vault_dir).resolve()
    matched_kis: list[dict[str, Any]] = []

    # Direct high-speed dual-file vault query (Rule 22 & Rule 40)
    if vault_root.exists() and vault_root.is_dir():
        q_lower = topic.lower().strip()
        for ki_dir in vault_root.iterdir():
            if not ki_dir.is_dir():
                continue
            meta_file = ki_dir / "metadata.json"
            if not meta_file.exists():
                continue
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                ki_id = meta.get("id") or meta.get("ki_id") or ki_dir.name
                title = meta.get("title", ki_id)
                summary = meta.get("summary", "")
                if not summary:
                    summary_file = ki_dir / "summary.md"
                    if summary_file.exists():
                        summary = summary_file.read_text(encoding="utf-8")
                tags = meta.get("tags") or []
                domain = meta.get("domain") or meta.get("category") or "general"
                isnad = meta.get("isnad") or {}
                status = (
                    isnad.get("status", "VERIFIED")
                    if isinstance(isnad, dict)
                    else getattr(isnad, "status", "VERIFIED")
                )
                edges = meta.get("edges") or []

                searchable = f"{title} {summary} {' '.join(tags)} {domain}".lower()
                if q_lower in searchable or not q_lower:
                    matched_kis.append({
                        "ki_id": ki_id,
                        "title": title,
                        "domain": domain,
                        "status": status,
                        "tags": list(tags),
                        "summary_preview": (summary or "").split("\n")[0][:100],
                        "edges": edges,
                    })
            except Exception:
                continue

    # Query Skill Graph intent routing
    skill_routing = route_skills_cmd(intent=topic, top_k=limit, root_path=root_path, context=ctx)
    matches = skill_routing.get("matches", [])

    # Map matched KIs
    ki_list_raw = matched_kis[:limit]

    # Map matched Skills (Rule 35: match entries are strictly keyed by 'skill_name')
    skill_list = []
    for s in matches[:limit]:
        s_name = s.get("skill_name") or s.get("name") or "unknown"
        skill_list.append({
            "skill_name": s_name,
            "confidence": s.get("confidence", 0.0),
            "cluster": s.get("cluster", "general"),
            "recommended_chain": s.get("recommended_chain", []),
        })

    # Lineage and cross-link discovery (prioritizing typed became_skill / distilled_from edges over heuristics)
    linked_pairs = []
    matched_ki_ids = set()
    matched_skill_names = set()

    for ki in ki_list_raw:
        k_text = (ki["title"] + " " + " ".join(ki["tags"]) + " " + ki["domain"]).lower()
        ki_edges = ki.get("edges") or []
        for sk in skill_list:
            sk_name = sk["skill_name"]
            sk_clean = sk_name.lower().strip()

            # 1. Check for typed graph edge (became_skill, distilled_from, implements)
            rel_type = None
            for edge in ki_edges:
                edge_type = edge.get("type")
                target = str(edge.get("target") or "").lower().strip()
                if edge_type in ("became_skill", "distilled_from", "implements") and (
                    target == sk_clean
                    or target == f".agents/skills/{sk_clean}"
                    or target.endswith(f"/{sk_clean}")
                    or sk_clean in target
                ):
                    rel_type = edge_type
                    break

            # 2. Heuristic domain/tag lineage fallback
            if not rel_type:
                sk_slug = sk_clean.replace("-", " ")
                if (
                    sk_slug in k_text
                    or any(t.lower() in sk_slug for t in ki["tags"])
                    or ki["domain"].lower() in sk_slug
                ):
                    rel_type = "domain_lineage"

            if rel_type:
                linked_pairs.append({
                    "ki_id": ki["ki_id"],
                    "skill_name": sk["skill_name"],
                    "relationship": rel_type,
                })
                matched_ki_ids.add(ki["ki_id"])
                matched_skill_names.add(sk["skill_name"])

    # Clean ki_list output removing internal edges
    ki_list = [{k: v for k, v in ki.items() if k != "edges"} for ki in ki_list_raw]

    unbridged_kis = [ki for ki in ki_list if ki["ki_id"] not in matched_ki_ids]
    ungrounded_skills = [sk for sk in skill_list if sk["skill_name"] not in matched_skill_names]

    return {
        "status": "ok",
        "topic": topic,
        "knowledge_items_count": len(ki_list),
        "skills_count": len(skill_list),
        "linked_pairs_count": len(linked_pairs),
        "knowledge_items": ki_list,
        "skills": skill_list,
        "linked_pairs": linked_pairs,
        "unbridged_kis": unbridged_kis,
        "ungrounded_skills": ungrounded_skills,
    }


__all__ = ["query_knowledge_and_skills"]
