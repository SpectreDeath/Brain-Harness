"""Graph traversal, neighbor discovery, and BFS shortest path algorithms (Rule 11, Rule 55)."""

from __future__ import annotations

from collections import deque
from typing import Any, Sequence

from harness.services.storage.models import KnowledgeItemRecord
from harness.services.storage.vault_graph_models import DerivedKnowledgeGraph


def find_node_neighbors(
    node_id: str,
    graph: DerivedKnowledgeGraph,
    *,
    max_depth: int = 1,
    edge_type: str | None = None,
    exclude_derived: bool = False,
) -> list[dict[str, Any]]:
    """Traverse and list adjacent entities up to max_depth (1..4) with edge direction and confidence."""
    depth_limit = max(1, min(4, max_depth))
    node_map = {n.id: n for n in graph.nodes}
    target_id = node_id.strip()
    if target_id not in node_map:
        return []

    visited: set[str] = {target_id}
    queue: deque[tuple[str, int]] = deque([(target_id, 0)])
    neighbors: list[dict[str, Any]] = []

    while queue:
        curr, d = queue.popleft()
        if d >= depth_limit:
            continue

        for e in graph.edges:
            if exclude_derived and e.derived:
                continue
            if edge_type and e.type != edge_type:
                continue

            if e.source == curr:
                other_id, direction = e.target, "outbound"
            elif e.target == curr:
                other_id, direction = e.source, "inbound"
            else:
                continue

            other_node = node_map.get(other_id)
            neighbors.append({
                "id": other_id,
                "label": other_node.label if other_node else other_id,
                "node_kind": other_node.node_kind if other_node else "unknown",
                "domain": other_node.domain if other_node else "general",
                "depth": d + 1,
                "direction": direction,
                "edge_type": e.type,
                "derived": e.derived,
                "confidence": e.confidence,
            })
            if other_id not in visited:
                visited.add(other_id)
                queue.append((other_id, d + 1))

    return neighbors


def bfs_shortest_path(
    from_id: str,
    to_id: str,
    graph: DerivedKnowledgeGraph,
    *,
    max_depth: int = 6,
    exclude_derived: bool = False,
    directed: bool = False,
) -> dict[str, Any]:
    """BFS shortest path across graph edges strictly enforcing Rule 55 (zero synthetic edges)."""
    src = from_id.strip()
    dst = to_id.strip()
    node_map = {n.id: n for n in graph.nodes}

    if src not in node_map or dst not in node_map:
        return {"status": "no_path", "chain": [], "length": 0, "hops": []}
    if src == dst:
        return {"status": "same_node", "chain": [src], "length": 0, "hops": []}

    visited: set[str] = {src}
    queue: deque[tuple[str, list[str], list[dict[str, Any]]]] = deque([(src, [src], [])])

    while queue:
        curr, chain, hops = queue.popleft()
        if len(chain) - 1 >= max_depth:
            continue

        for e in graph.edges:
            if exclude_derived and e.derived:
                continue

            if e.source == curr:
                nxt, direction = e.target, "forward"
            elif not directed and e.target == curr:
                nxt, direction = e.source, "reverse"
            else:
                continue

            hop_meta = {
                "from": curr,
                "to": nxt,
                "edge_type": e.type,
                "direction": direction,
                "derived": e.derived,
                "confidence": e.confidence,
            }

            if nxt == dst:
                return {
                    "status": "found",
                    "chain": chain + [nxt],
                    "length": len(chain),
                    "hops": hops + [hop_meta],
                }

            if nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, chain + [nxt], hops + [hop_meta]))

    return {"status": "no_path", "chain": [], "length": 0, "hops": []}


def find_vault_orphans(
    graph: DerivedKnowledgeGraph,
    items: Sequence[KnowledgeItemRecord],
) -> dict[str, Any]:
    """Find isolated KIs and disconnected components with missing-field profiles."""
    incident_nodes = {e.source for e in graph.edges} | {e.target for e in graph.edges}
    isolated_items = []
    untagged_count = 0
    uncategorized_count = 0
    missing_source_count = 0

    for ki in items:
        if ki.id not in incident_nodes:
            is_untagged = len(ki.tags) == 0
            is_uncat = ki.category == "general" or not ki.category
            is_missing_src = not bool(ki.source_target)

            if is_untagged:
                untagged_count += 1
            if is_uncat:
                uncategorized_count += 1
            if is_missing_src:
                missing_source_count += 1

            isolated_items.append({
                "id": ki.id,
                "title": ki.title,
                "category": ki.category,
                "tags_count": len(ki.tags),
                "has_source": bool(ki.source_target),
                "created_at": ki.created_at,
            })

    return {
        "isolated_count": len(isolated_items),
        "isolated_items": isolated_items,
        "profiles": {
            "untagged": untagged_count,
            "uncategorized": uncategorized_count,
            "missing_source": missing_source_count,
        },
    }

