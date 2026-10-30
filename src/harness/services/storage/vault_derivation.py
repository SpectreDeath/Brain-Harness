"""Authoritative knowledge graph derivation engine and census metrics."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Sequence

from harness.services.storage.models import KnowledgeItemRecord
from harness.services.storage.vault_graph_models import (
    DerivedKnowledgeGraph,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    KnowledgeGraphSummary,
)
from harness.services.storage.vault_taxonomy import get_taxonomy_domain


def derive_knowledge_graph(
    items: Sequence[KnowledgeItemRecord],
    *,
    nodes_filter: str = "all",
    include_single_tag_edges: bool = False,
    include_shared_source: bool = False,
    max_tag_freq: float = 0.15,
    min_confidence: float = 0.0,
) -> DerivedKnowledgeGraph:
    """Derive authoritative knowledge graph across items, skills, code paths, and taxonomic links."""
    total_items = len(items)
    tag_counts = Counter(t for ki in items for t in set(ki.tags))
    excluded_mega_tags = tuple(sorted(t for t, c in tag_counts.items() if total_items > 0 and (c / total_items) > max_tag_freq))
    excluded_set = set(excluded_mega_tags)

    nodes: dict[str, KnowledgeGraphNode] = {}
    for ki in items:
        dom = get_taxonomy_domain(ki.category)
        nodes[ki.id] = KnowledgeGraphNode(
            id=ki.id, label=ki.title, node_kind="ki", category=ki.category, domain=dom,
            tags=tuple(ki.tags), status=ki.status, retrieval_count=ki.retrieval_count,
            success_count=ki.success_count, created_at=ki.created_at, source_target=ki.source_target,
        )

    edges: list[KnowledgeGraphEdge] = []
    existing_pairs: set[tuple[str, str, str]] = set()

    for ki in items:
        for e in ki.edges:
            if nodes_filter == "ki-only" and e.target_kind != "ki":
                continue
            if e.confidence < min_confidence:
                continue
            pair_key = (ki.id, e.target, e.type)
            if pair_key not in existing_pairs:
                existing_pairs.add(pair_key)
                edges.append(KnowledgeGraphEdge(
                    source=ki.id, target=e.target, target_kind=e.target_kind, type=e.type,
                    derived=e.derived, confidence=e.confidence, shared_tags=(), description=e.description or "",
                ))
            if nodes_filter == "all" and e.target not in nodes:
                label = Path(e.target).name if "/" in e.target or "\\" in e.target else e.target
                nodes[e.target] = KnowledgeGraphNode(
                    id=e.target, label=label, node_kind=e.target_kind, category=e.target_kind,
                    domain=e.target_kind, status="EXTERNAL",
                )

    n = len(items)
    for i in range(n):
        a = items[i]
        dom_a = get_taxonomy_domain(a.category)
        tags_a = set(a.tags) - excluded_set
        for j in range(i + 1, n):
            b = items[j]
            dom_b = get_taxonomy_domain(b.category)
            if dom_a == dom_b and dom_a != "general":
                tags_b = set(b.tags) - excluded_set
                shared = tags_a & tags_b
                if len(shared) >= 2 or (include_single_tag_edges and len(shared) == 1):
                    conf = 0.80 if len(shared) >= 2 else 0.60
                    if conf >= min_confidence and (a.id, b.id, "same_domain") not in existing_pairs and (b.id, a.id, "same_domain") not in existing_pairs:
                        existing_pairs.add((a.id, b.id, "same_domain"))
                        edges.append(KnowledgeGraphEdge(
                            source=a.id, target=b.id, target_kind="ki", type="same_domain",
                            derived=True, confidence=conf, shared_tags=tuple(sorted(shared)),
                            description=f"Shared tags: {', '.join(sorted(shared))}",
                        ))
            if include_shared_source and a.source_target and a.source_target == b.source_target:
                if 0.75 >= min_confidence and (a.id, b.id, "shared_source") not in existing_pairs and (b.id, a.id, "shared_source") not in existing_pairs:
                    existing_pairs.add((a.id, b.id, "shared_source"))
                    edges.append(KnowledgeGraphEdge(
                        source=a.id, target=b.id, target_kind="ki", type="shared_source",
                        derived=True, confidence=0.75, description=f"Shared source: {a.source_target}",
                    ))

    # Census and component metrics
    adj: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        adj[edge.source].add(edge.target)
        adj[edge.target].add(edge.source)

    visited: set[str] = set()
    components: list[list[str]] = []
    ki_ids = {k.id for k in items}
    for kid in sorted(ki_ids):
        if kid not in visited:
            comp, q = [], [kid]
            visited.add(kid)
            while q:
                curr = q.pop()
                comp.append(curr)
                for neighbor in adj[curr]:
                    if neighbor in ki_ids and neighbor not in visited:
                        visited.add(neighbor)
                        q.append(neighbor)
            components.append(comp)

    components.sort(key=len, reverse=True)
    isolated_count = sum(1 for c in components if len(c) == 1)
    edge_type_counts = Counter(e.type for e in edges)
    non_ki_counts = Counter(n.node_kind for n in nodes.values() if n.node_kind != "ki")

    summary = KnowledgeGraphSummary(
        total_nodes=len(nodes),
        ki_nodes=total_items,
        non_ki_nodes_by_kind=dict(non_ki_counts),
        total_edges=len(edges),
        edges_by_type=dict(edge_type_counts),
        derived_edge_count=sum(1 for e in edges if e.derived),
        asserted_edge_count=sum(1 for e in edges if not e.derived),
        component_count=len(components),
        largest_component_size=len(components[0]) if components else 0,
        isolated_ki_count=isolated_count,
        untagged_ki_count=sum(1 for k in items if not k.tags),
        uncategorized_ki_count=sum(1 for k in items if not k.category or k.category == "general"),
        excluded_mega_tags=excluded_mega_tags,
        date_coverage_count=sum(1 for k in items if bool(k.created_at)),
    )

    return DerivedKnowledgeGraph(nodes=tuple(nodes.values()), edges=tuple(edges), summary=summary)

