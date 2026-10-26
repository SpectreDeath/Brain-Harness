"""Knowledge graph query service, edge backfilling, and link suggestion."""

from __future__ import annotations

from typing import Any, Sequence

from harness.services.storage.models import KnowledgeEdge, KnowledgeItemRecord
from harness.services.storage.vault_taxonomy import get_taxonomy_domain


class KnowledgeGraphQueryService:
    """Provides topological traversal and edge-based queries over Knowledge Vault items."""

    def get_skill_lineage(self, skill_name: str, items: Sequence[KnowledgeItemRecord]) -> list[str]:
        """Return list of KI IDs that fed into or were distilled to form the specified skill."""
        lineage: list[str] = []
        target = skill_name.lower().strip()
        for ki in items:
            has_edge = any(e.type == "became_skill" and e.target.lower() == target for e in ki.edges)
            if has_edge or ki.anchors.get("target_skill", "").lower() == target or f"skill:{target}" in [t.lower() for t in ki.tags]:
                lineage.append(ki.id)
        return sorted(set(lineage))

    def get_dependents(self, node_id: str, items: Sequence[KnowledgeItemRecord]) -> list[dict[str, Any]]:
        """Return all items, skills, or plugins that point to or depend upon node_id."""
        dependents: list[dict[str, Any]] = []
        target = node_id.lower().strip()
        for ki in items:
            for edge in ki.edges:
                if edge.target.lower() == target:
                    dependents.append({"source_ki": ki.id, "edge_type": edge.type, "target_kind": edge.target_kind, "confidence": edge.confidence})
        return dependents

    def get_contradictions(self, ki_id: str, items: Sequence[KnowledgeItemRecord]) -> list[str]:
        """Return list of KI IDs that contradict or supersede the given item."""
        conflicting: list[str] = []
        for ki in items:
            if ki.id == ki_id:
                for edge in ki.edges:
                    if edge.type in ("contradicts", "supersedes"):
                        conflicting.append(edge.target)
            else:
                for edge in ki.edges:
                    if edge.target == ki_id and edge.type in ("contradicts", "supersedes"):
                        conflicting.append(ki.id)
                if ki.superseded_by == ki_id:
                    conflicting.append(ki.id)
        return sorted(set(conflicting))

    def get_topic_neighborhood(self, topic: str, items: Sequence[KnowledgeItemRecord]) -> dict[str, Any]:
        """Return subgraph of KIs, skills, and code references related to a topic or domain."""
        t_norm = topic.lower().strip()
        matched_kis: list[str] = []
        skills: set[str] = set()
        paths: set[str] = set()

        for ki in items:
            domain = get_taxonomy_domain(ki.category)
            if t_norm in domain or t_norm in ki.category.lower() or t_norm in [t.lower() for t in ki.tags] or t_norm in ki.title.lower():
                matched_kis.append(ki.id)
                for edge in ki.edges:
                    if edge.target_kind == "skill":
                        skills.add(edge.target)
                    elif edge.target_kind == "path":
                        paths.add(edge.target)

        return {"topic": topic, "matched_kis": matched_kis, "skills": sorted(skills), "paths": sorted(paths)}

    def propose_links(self, ki: KnowledgeItemRecord, existing: Sequence[KnowledgeItemRecord]) -> list[KnowledgeEdge]:
        """Propose candidate relationship edges for a new or unlinked Knowledge Item."""
        proposed: list[KnowledgeEdge] = []
        domain = get_taxonomy_domain(ki.category)
        tags = set(ki.tags)

        if ki.source_target and ("src/" in ki.source_target or "plugins/" in ki.source_target):
            proposed.append(KnowledgeEdge(type="references_code", target=ki.source_target, target_kind="path", derived=True, confidence=0.95))

        target_skill = ki.anchors.get("target_skill")
        if target_skill:
            proposed.append(KnowledgeEdge(type="became_skill", target=target_skill, target_kind="skill", confidence=1.0))

        for other in existing:
            if other.id == ki.id:
                continue
            if other.id == ki.superseded_by:
                proposed.append(KnowledgeEdge(type="superseded_by", target=other.id, target_kind="ki", derived=True, confidence=0.99))
            elif len(tags & set(other.tags)) >= 2 and domain == get_taxonomy_domain(other.category) and domain != "general":
                proposed.append(KnowledgeEdge(type="same_domain", target=other.id, target_kind="ki", derived=True, confidence=0.80))

        return proposed

    def backfill_edges_mechanically(self, items: Sequence[KnowledgeItemRecord]) -> int:
        """Derive and attach mechanical lineage edges across existing Knowledge Items in-place."""
        added = 0
        for ki in items:
            if ki.source_target and ("src/" in ki.source_target or "plugins/" in ki.source_target):
                if not any(e.type == "references_code" and e.target == ki.source_target for e in ki.edges):
                    ki.add_edge("references_code", ki.source_target, target_kind="path", derived=True, confidence=0.95)
                    added += 1

            target_skill = ki.anchors.get("target_skill")
            if target_skill and not any(e.type == "became_skill" for e in ki.edges):
                ki.add_edge("became_skill", target_skill, target_kind="skill", derived=True, confidence=0.95)
                added += 1

            if ki.superseded_by and not any(e.type == "supersedes" and e.target == ki.superseded_by for e in ki.edges):
                ki.add_edge("supersedes", ki.superseded_by, target_kind="ki", derived=True, confidence=1.0)
                added += 1
        return added

