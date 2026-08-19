"""Topological sort — pure graph utility for dependency resolution.

Extracted from PluginLifecycle so the algorithm can be tested independently
of plugin state machines and is not hidden inside a class method.
"""

from __future__ import annotations

from harness.kernel.lifecycle import CyclicDependencyError


def topological_sort(
    nodes: list[str],
    edges: dict[str, set[str]],
) -> list[str]:
    """Kahn's topological sort over a dependency graph.

    Args:
        nodes: All nodes that should appear in the output.
        edges: Adjacency dict where ``edges[A] = {B, C}`` means A depends on
               B and C -- so B and C must come *before* A in the output.

    Returns:
        Nodes in dependency-safe order (dependencies first).

    Raises:
        CyclicDependencyError: If a cycle is detected.

    Example::

        topological_sort(
            nodes=["a", "b", "c"],
            edges={"b": {"a"}, "c": {"b"}},
        )
        # -> ["a", "b", "c"]
    """
    # in_degree[n] = number of nodes that must come before n
    in_degree: dict[str, int] = {n: 0 for n in nodes}
    # dependents[dep] = list of nodes that depend on dep
    dependents: dict[str, list[str]] = {n: [] for n in nodes}

    for node, deps in edges.items():
        if node not in in_degree:
            continue  # node not in our target set; skip
        for dep in deps:
            if dep not in in_degree:
                continue  # dep not in our target set; ignore
            in_degree[node] += 1
            dependents[dep].append(node)

    # Start with all nodes that have no outstanding dependencies
    queue: list[str] = [n for n in nodes if in_degree[n] == 0]
    order: list[str] = []

    while queue:
        node = queue.pop(0)
        order.append(node)
        for dependent in dependents[node]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(order) != len(nodes):
        remaining = [n for n in nodes if n not in set(order)]
        raise CyclicDependencyError(remaining)

    return order
