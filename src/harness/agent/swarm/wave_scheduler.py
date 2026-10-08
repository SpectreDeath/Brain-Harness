"""Topological wave dependency partitioning, cycle prevention, and wave execution scheduling."""

from __future__ import annotations

from typing import Any

from harness.agent.swarm.models import SwarmDAG
from harness.kernel.graph import DependencyGraph, GraphCycleError


class SwarmWaveScheduler:
    """Isolates topological dependency wave partitioning and wave scheduling."""

    def compute_waves(self, dag: SwarmDAG) -> list[list[str]]:
        """Partition SwarmDAG nodes into topological execution waves.

        Raises:
            ValueError: If a cyclic dependency or missing dependency is detected.
        """
        for node_id, node in dag.nodes.items():
            for dep in node.dependencies:
                if dep not in dag.nodes:
                    raise ValueError(
                        f"Node '{node_id}' references non-existent dependency '{dep}'"
                    )

        graph = dag.to_dependency_graph()
        try:
            return graph.execution_waves()
        except GraphCycleError as e:
            raise ValueError(
                f"Cycle detected in SwarmDAG task dependencies: {e}"
            ) from e

    def validate_dag(self, dag: SwarmDAG) -> bool:
        """Return True if DAG is valid and acyclic, raises ValueError otherwise."""
        self.compute_waves(dag)
        return True


__all__ = ["SwarmWaveScheduler"]
