"""Topological pathfinding, DAG cycle prevention, and reachability routing (Rule 55)."""

from __future__ import annotations

import collections
from typing import Any


def _would_create_cycle(adj: dict[str, set[str]], src: str, dst: str) -> bool:
    """Return True if adding src->dst would create a directed cycle via DFS reachability."""
    visited: set[str] = set()
    stack = [dst]
    while stack:
        node = stack.pop()
        if node == src:
            return True
        if node not in visited:
            visited.add(node)
            stack.extend(adj.get(node, set()))
    return False


def find_shortest_path(
    adj: dict[str, set[str]],
    start: str,
    target: str,
    valid_nodes: set[str] | None = None,
) -> list[str] | None:
    """Compute shortest directed path from start to target using BFS without synthetic fallback (Rule 55)."""
    if start == target:
        return [start]

    queue: collections.deque[list[str]] = collections.deque([[start]])
    visited: set[str] = {start}

    while queue:
        path = queue.popleft()
        curr = path[-1]

        neighbors = adj.get(curr, set())
        for neighbor in sorted(neighbors):
            if neighbor == target:
                return path + [neighbor]
            if neighbor not in visited and (valid_nodes is None or neighbor in valid_nodes):
                visited.add(neighbor)
                queue.append(path + [neighbor])

    return None


def compute_prerequisite_closure(
    clean_name: str,
    adj_in: dict[str, list[Any]],
    valid_nodes: set[str],
) -> list[str]:
    """Compute the full transitive prerequisite closure for a skill in topological execution order."""
    prereqs: list[str] = []
    visited: set[str] = set()

    def _traverse(node: str) -> None:
        for edge in adj_in.get(node, []):
            edge_src = getattr(edge, "source", None)
            rel = str(getattr(edge, "relation", ""))
            if edge_src and edge_src in valid_nodes and edge_src not in visited:
                if "PRECEDES" in rel:
                    visited.add(edge_src)
                    _traverse(edge_src)
                    prereqs.append(edge_src)

    _traverse(clean_name)
    return list(dict.fromkeys(prereqs))


would_create_cycle = _would_create_cycle

__all__ = [
    "_would_create_cycle",
    "would_create_cycle",
    "compute_prerequisite_closure",
    "find_shortest_path",
]
