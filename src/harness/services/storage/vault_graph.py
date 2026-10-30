"""Knowledge graph query service, edge backfilling, and link suggestion."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.storage.models import KnowledgeEdge, KnowledgeItemRecord
from harness.services.storage.vault_backfill import (
    backfill_edges_mechanically as _backfill_edges_mechanically,
    propose_links as _propose_links,
)
from harness.services.storage.vault_derivation import derive_knowledge_graph
from harness.services.storage.vault_traversal import (
    bfs_shortest_path,
    find_node_neighbors,
    find_vault_orphans,
)
from harness.services.storage.vault_graph_models import (
    DerivedKnowledgeGraph,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    KnowledgeGraphSummary,
)
from harness.services.storage.vault_taxonomy import get_taxonomy_domain

KNOWLEDGE_GRAPH_SERVICE_KEY: ServiceKey[KnowledgeGraphQueryService] = ServiceKey("service.knowledge_graph_query")


def resolve_knowledge_graph_service(context: ServiceContext | None = None) -> KnowledgeGraphQueryService:
    """Resolve KnowledgeGraphQueryService from IoC container or instantiate default fallback (Rule 58)."""
    if context is not None:
        service = context.optional(KNOWLEDGE_GRAPH_SERVICE_KEY)
        if service is not None:
            return service
    return KnowledgeGraphQueryService()


def validate_export_path(out_path: Path | str, vault_dir: Path | str = ".harness/knowledge") -> Path:
    """Enforce export path guardrail: reject outputs resolving inside vault root (Rule 40)."""
    target = Path(out_path).resolve()
    vault = Path(vault_dir).resolve()
    try:
        target.relative_to(vault)
        raise ValueError(
            f"Export target path '{out_path}' resolves inside knowledge vault directory '{vault}'. "
            "Flat export files inside .harness/knowledge/ are forbidden by Rule 40."
        )
    except ValueError as e:
        if "forbidden by Rule 40" in str(e):
            raise
    return target


class KnowledgeGraphQueryService:
    """Provides topological traversal and edge-based queries over Knowledge Vault items."""

    def derive_graph(
        self,
        items: Sequence[KnowledgeItemRecord],
        *,
        nodes_filter: str = "all",
        include_single_tag_edges: bool = False,
        include_shared_source: bool = False,
        max_tag_freq: float = 0.15,
        min_confidence: float = 0.0,
    ) -> DerivedKnowledgeGraph:
        """Derive authoritative knowledge graph across items, skills, code paths, and taxonomic links."""
        return derive_knowledge_graph(
            items,
            nodes_filter=nodes_filter,
            include_single_tag_edges=include_single_tag_edges,
            include_shared_source=include_shared_source,
            max_tag_freq=max_tag_freq,
            min_confidence=min_confidence,
        )

    def get_skill_lineage(self, skill_name: str, items: Sequence[KnowledgeItemRecord]) -> list[str]:
        target = skill_name.lower().strip()
        lineage = [
            ki.id for ki in items
            if any(e.type == "became_skill" and e.target.lower() == target for e in ki.edges)
            or ki.anchors.get("target_skill", "").lower() == target
            or f"skill:{target}" in [t.lower() for t in ki.tags]
        ]
        return sorted(set(lineage))

    def get_dependents(self, node_id: str, items: Sequence[KnowledgeItemRecord]) -> list[dict[str, Any]]:
        target = node_id.lower().strip()
        return [
            {"source_ki": ki.id, "edge_type": e.type, "target_kind": e.target_kind, "confidence": e.confidence}
            for ki in items for e in ki.edges if e.target.lower() == target
        ]

    def get_contradictions(self, ki_id: str, items: Sequence[KnowledgeItemRecord]) -> list[str]:
        conflicting: list[str] = []
        for ki in items:
            if ki.id == ki_id:
                conflicting.extend(e.target for e in ki.edges if e.type in ("contradicts", "supersedes"))
            else:
                if any(e.target == ki_id and e.type in ("contradicts", "supersedes") for e in ki.edges):
                    conflicting.append(ki.id)
                elif ki.superseded_by == ki_id:
                    conflicting.append(ki.id)
        return sorted(set(conflicting))

    def get_topic_neighborhood(self, topic: str, items: Sequence[KnowledgeItemRecord]) -> dict[str, Any]:
        t_norm = topic.lower().strip()
        matched, skills, paths = [], set(), set()
        for ki in items:
            domain = get_taxonomy_domain(ki.category)
            if t_norm in domain or t_norm in ki.category.lower() or t_norm in [t.lower() for t in ki.tags] or t_norm in ki.title.lower():
                matched.append(ki.id)
                for e in ki.edges:
                    if e.target_kind == "skill":
                        skills.add(e.target)
                    elif e.target_kind == "path":
                        paths.add(e.target)
        return {"topic": topic, "matched_kis": matched, "skills": sorted(skills), "paths": sorted(paths)}

    def propose_links(
        self,
        ki: KnowledgeItemRecord,
        existing: Sequence[KnowledgeItemRecord],
        *,
        max_tag_freq: float = 0.15,
    ) -> list[KnowledgeEdge]:
        return _propose_links(ki, existing, max_tag_freq=max_tag_freq)

    def backfill_edges_mechanically(
        self,
        items: Sequence[KnowledgeItemRecord],
        vault_dir: Path | str = ".harness/knowledge",
        max_tag_freq: float = 0.15,
        dry_run: bool = False,
    ) -> int:
        res = _backfill_edges_mechanically(items, vault_dir=vault_dir, max_tag_freq=max_tag_freq, dry_run=dry_run)
        return int(res["total_added"])

    def backfill_edges_report(
        self,
        items: Sequence[KnowledgeItemRecord],
        vault_dir: Path | str = ".harness/knowledge",
        max_tag_freq: float = 0.15,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        return _backfill_edges_mechanically(items, vault_dir=vault_dir, max_tag_freq=max_tag_freq, dry_run=dry_run)

    def find_path(
        self,
        from_id: str,
        to_id: str,
        graph: DerivedKnowledgeGraph,
        *,
        max_depth: int = 6,
        exclude_derived: bool = False,
        directed: bool = False,
    ) -> dict[str, Any]:
        return bfs_shortest_path(from_id, to_id, graph, max_depth=max_depth, exclude_derived=exclude_derived, directed=directed)

    def get_neighbors(
        self,
        node_id: str,
        graph: DerivedKnowledgeGraph,
        *,
        depth: int = 1,
        edge_type: str | None = None,
        exclude_derived: bool = False,
    ) -> list[dict[str, Any]]:
        return find_node_neighbors(node_id, graph, max_depth=depth, edge_type=edge_type, exclude_derived=exclude_derived)

    def get_orphans(
        self,
        graph: DerivedKnowledgeGraph,
        items: Sequence[KnowledgeItemRecord],
    ) -> dict[str, Any]:
        return find_vault_orphans(graph, items)
