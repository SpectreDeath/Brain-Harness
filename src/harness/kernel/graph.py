"""Topological dependency graph engine and parallel wave scheduler.

Provides an authoritative, generic Directed Acyclic Graph (DAG) abstraction for
dependency resolution, cycle detection, parallel wave execution, and transitive
closure queries across the Harness kernel, agent swarms, and plugin lifecycles.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class CyclicDependencyError(Exception):
    """Raised when a dependency cycle is detected in a graph."""

    def __init__(self, cycle: list[Any] | None = None, message: str | None = None) -> None:
        self.cycle = cycle or []
        if message:
            super().__init__(message)
        elif self.cycle:
            chain = " → ".join(str(n) for n in self.cycle)
            super().__init__(f"Cyclic dependency detected: {chain}")
        else:
            super().__init__("Cyclic dependency detected in graph")


class GraphCycleError(CyclicDependencyError):
    """Semantic graph cycle detection error."""
    pass


class GraphDependencyError(Exception):
    """Raised when an unsatisfied or missing dependency is encountered in a graph."""

    def __init__(self, node: Any, missing: list[Any]) -> None:
        self.node = node
        self.missing = missing
        super().__init__(f"Node {node!r} has unsatisfied dependencies: {missing}")


class DependencyGraph(Generic[T]):
    """Generic Directed Acyclic Graph (DAG) for dependency resolution and execution scheduling.

    Edges represent dependency relationships: ``add_edge(from_node, to_node)`` declares
    that ``to_node`` depends on ``from_node`` (so ``from_node`` must execute/load before ``to_node``).

    Example::

        graph = DependencyGraph[str]()
        graph.add_edge("database", "api_service")
        graph.add_edge("api_service", "web_ui")

        waves = graph.execution_waves()
        # -> [["database"], ["api_service"], ["web_ui"]]
    """

    def __init__(self) -> None:
        self._nodes: dict[T, Any] = {}
        # _dependencies[to_node] = set of from_nodes that to_node depends upon (must come before to_node)
        self._dependencies: dict[T, set[T]] = defaultdict(set)
        # _dependents[from_node] = set of to_nodes that depend on from_node (must come after from_node)
        self._dependents: dict[T, set[T]] = defaultdict(set)

    def add_node(self, node: T, data: Any = None) -> None:
        """Add a node with optional payload data."""
        if node not in self._nodes:
            self._nodes[node] = data
            # Ensure keys exist in adjacency sets
            _ = self._dependencies[node]
            _ = self._dependents[node]
        elif data is not None:
            self._nodes[node] = data

    def add_edge(self, from_node: T, to_node: T) -> None:
        """Declare that ``to_node`` depends on ``from_node``.

        ``from_node`` must be resolved/executed before ``to_node``.
        """
        self.add_node(from_node)
        self.add_node(to_node)
        self._dependencies[to_node].add(from_node)
        self._dependents[from_node].add(to_node)

    def add_dependency(self, node: T, depends_on: T) -> None:
        """Convenience alias: declare that ``node`` depends on ``depends_on``."""
        self.add_edge(from_node=depends_on, to_node=node)

    def has_node(self, node: T) -> bool:
        """Return True if the node is in the graph."""
        return node in self._nodes

    def get_node_data(self, node: T) -> Any:
        """Retrieve the payload data associated with a node."""
        return self._nodes.get(node)

    @property
    def nodes(self) -> list[T]:
        """Return a list of all nodes in the graph."""
        return list(self._nodes.keys())

    @property
    def node_count(self) -> int:
        """Return the number of nodes in the graph."""
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        """Return the total number of directed edges in the graph."""
        return sum(len(deps) for deps in self._dependencies.values())

    def dependencies_of(self, node: T) -> set[T]:
        """Return immediate prerequisites of ``node``."""
        return set(self._dependencies.get(node, set()))

    def dependents_of(self, node: T) -> set[T]:
        """Return immediate dependents that rely on ``node``."""
        return set(self._dependents.get(node, set()))

    def transitive_dependencies(self, node: T) -> set[T]:
        """Return the transitive closure of all prerequisites for ``node``."""
        visited: set[T] = set()
        queue = deque([node])
        while queue:
            curr = queue.popleft()
            for dep in self._dependencies.get(curr, set()):
                if dep not in visited and dep != node:
                    visited.add(dep)
                    queue.append(dep)
        return visited

    def transitive_dependents(self, node: T) -> set[T]:
        """Return the transitive closure of all downstream nodes that depend on ``node``."""
        visited: set[T] = set()
        queue = deque([node])
        while queue:
            curr = queue.popleft()
            for dependent in self._dependents.get(curr, set()):
                if dependent not in visited and dependent != node:
                    visited.add(dependent)
                    queue.append(dependent)
        return visited

    def roots(self) -> list[T]:
        """Return nodes that have no prerequisites (in-degree == 0)."""
        return [node for node in self._nodes if not self._dependencies[node]]

    def leaves(self) -> list[T]:
        """Return nodes that have no dependents (out-degree == 0)."""
        return [node for node in self._nodes if not self._dependents[node]]

    def detect_cycle(self) -> list[T] | None:
        """Detect if the graph contains any cycle.

        Returns:
            A list representing the cycle path (e.g. ``[A, B, C, A]``) if a cycle exists,
            or ``None`` if the graph is a valid DAG.
        """
        # Tarjan / DFS cycle finder
        visited: dict[T, int] = {}  # 0 = unvisited, 1 = visiting, 2 = visited
        parent: dict[T, T | None] = {}

        for root in self._nodes:
            if visited.get(root, 0) != 0:
                continue

            stack: list[tuple[T, list[T]]] = [(root, list(self._dependents.get(root, set())))]
            visited[root] = 1

            while stack:
                curr, neighbors = stack[-1]
                if neighbors:
                    nxt = neighbors.pop()
                    state = visited.get(nxt, 0)
                    if state == 1:
                        # Cycle found! Reconstruct cycle path
                        cycle = [nxt, curr]
                        for s_node, _ in reversed(stack[:-1]):
                            cycle.append(s_node)
                            if s_node == nxt:
                                break
                        cycle.reverse()
                        return cycle
                    if state == 0:
                        visited[nxt] = 1
                        parent[nxt] = curr
                        stack.append((nxt, list(self._dependents.get(nxt, set()))))
                else:
                    visited[curr] = 2
                    stack.pop()

        return None

    def execution_waves(self) -> list[list[T]]:
        """Compute parallel execution waves using level-order Kahn's topological sort.

        Returns:
            A list of waves, where each wave is a list of nodes whose dependencies have
            all been satisfied by earlier waves.

        Raises:
            GraphCycleError: If the graph contains a cyclic dependency.
        """
        in_degree: dict[T, int] = {node: len(self._dependencies[node]) for node in self._nodes}
        ready: deque[T] = deque([node for node, deg in in_degree.items() if deg == 0])

        waves: list[list[T]] = []
        processed_count = 0

        while ready:
            wave = list(ready)
            ready.clear()
            waves.append(wave)
            processed_count += len(wave)

            for node in wave:
                for dependent in self._dependents.get(node, set()):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        ready.append(dependent)

        if processed_count != len(self._nodes):
            cycle = self.detect_cycle()
            if not cycle:
                # Fallback to remaining unprocessed nodes
                cycle = [n for n in self._nodes if in_degree[n] > 0]
            raise GraphCycleError(cycle)

        return waves

    def topological_sort(self) -> list[T]:
        """Compute a flat, linear topological ordering of nodes.

        Returns:
            Nodes sorted in dependency order (prerequisites first).

        Raises:
            GraphCycleError: If the graph contains a cyclic dependency.
        """
        waves = self.execution_waves()
        return [node for wave in waves for node in wave]

    def to_mermaid(self, direction: str = "TD") -> str:
        """Export the graph as a Mermaid flowchart diagram."""
        lines = [f"graph {direction}"]
        for node in sorted(self._nodes.keys(), key=str):
            clean_node = str(node).replace('"', '\\"')
            lines.append(f'    "{clean_node}"')
        for to_node, from_nodes in self._dependencies.items():
            clean_to = str(to_node).replace('"', '\\"')
            for from_node in sorted(from_nodes, key=str):
                clean_from = str(from_node).replace('"', '\\"')
                lines.append(f'    "{clean_from}" --> "{clean_to}"')
        return "\n".join(lines)


# Type alias
DAG = DependencyGraph


def topological_sort(
    nodes: list[str],
    edges: dict[str, set[str]],
) -> list[str]:
    """Kahn's topological sort over a dependency graph (backward compatible procedural interface).

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
    graph = DependencyGraph[str]()
    for n in nodes:
        graph.add_node(n)

    for node, deps in edges.items():
        if not graph.has_node(node):
            continue
        for dep in deps:
            if graph.has_node(dep):
                # node depends on dep (dep -> node)
                graph.add_edge(from_node=dep, to_node=node)

    return graph.topological_sort()
