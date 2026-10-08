"""Typed models, DAG definitions, and telemetry structures for Swarm execution (Rule 12)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from harness.kernel.graph import DependencyGraph, GraphCycleError


@dataclass(slots=True)
class SwarmNode:
    """A discrete unit of work in a multi-agent swarm DAG."""

    id: str
    role: str
    task: str
    dependencies: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    allocated_tokens: int = 10_000
    status: str = "pending"  # "pending", "running", "completed", "failed", "skipped"
    result: Any = None
    error: str | None = None
    tokens_used: int = 0

    def __post_init__(self) -> None:
        if self.allocated_tokens < 0:
            raise ValueError(
                f"allocated_tokens must be non-negative, got {self.allocated_tokens}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "task": self.task,
            "dependencies": self.dependencies,
            "tools": self.tools,
            "allocated_tokens": self.allocated_tokens,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "tokens_used": self.tokens_used,
        }


class SwarmDAG:
    """Directed Acyclic Graph representing task dependencies among swarm agents."""

    def __init__(self) -> None:
        self.nodes: dict[str, SwarmNode] = {}

    def add_node(self, node: SwarmNode) -> None:
        """Add a node to the DAG."""
        self.nodes[node.id] = node

    def add_edge(self, from_node_id: str, to_node_id: str) -> None:
        """Declare that to_node depends on from_node."""
        if to_node_id not in self.nodes:
            raise KeyError(f"Target node '{to_node_id}' does not exist in DAG")
        if from_node_id not in self.nodes:
            raise KeyError(f"Source node '{from_node_id}' does not exist in DAG")
        if from_node_id not in self.nodes[to_node_id].dependencies:
            self.nodes[to_node_id].dependencies.append(from_node_id)

    def to_dependency_graph(self) -> DependencyGraph[str]:
        """Convert SwarmDAG into an authoritative DependencyGraph instance."""
        graph = DependencyGraph[str]()
        for node_id, node in self.nodes.items():
            graph.add_node(node_id, data=node)

        for node_id, node in self.nodes.items():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    raise ValueError(
                        f"Node '{node_id}' references non-existent dependency '{dep}'"
                    )
                graph.add_edge(from_node=dep, to_node=node_id)

        return graph

    def get_execution_plan(self) -> list[list[str]]:
        """Compute parallel execution waves via topological sorting.

        Raises:
            ValueError: If a cyclic dependency is detected.
        """
        graph = self.to_dependency_graph()
        try:
            return graph.execution_waves()
        except GraphCycleError as e:
            raise ValueError(
                f"Cycle detected in SwarmDAG task dependencies: {e}"
            ) from e

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "node_count": len(self.nodes),
        }


@dataclass
class SwarmNodeExecution:
    """Detailed execution telemetry for an individual Swarm DAG node."""

    id: str
    role: str
    task: str
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    tokens_used: int = 0
    result: Any = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "task": self.task,
            "dependencies": list(self.dependencies),
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": round(self.duration, 4),
            "tokens_used": self.tokens_used,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class SwarmWaveMetrics:
    """Telemetry for a parallel wave of node executions in the Swarm DAG."""

    wave_index: int
    node_ids: list[str]
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    total_tokens: int = 0
    bottleneck_node_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "wave_index": self.wave_index,
            "node_ids": list(self.node_ids),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": round(self.duration, 4),
            "total_tokens": self.total_tokens,
            "bottleneck_node_id": self.bottleneck_node_id,
        }


@dataclass
class SwarmExecutionTree:
    """Hierarchical execution telemetry, critical path analysis, and wave metrics for a Swarm run."""

    run_id: str
    objective: str
    status: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    total_tokens: int = 0
    nodes: dict[str, SwarmNodeExecution] = field(default_factory=dict)
    waves: list[SwarmWaveMetrics] = field(default_factory=list)
    critical_path: list[str] = field(default_factory=list)
    critical_path_duration: float = 0.0
    bottlenecks: list[dict[str, Any]] = field(default_factory=list)

    def calculate_critical_path(self) -> list[str]:
        """Compute the sequence of dependent nodes that determined the maximum cumulative latency path."""
        if not self.nodes:
            return []

        memo: dict[str, tuple[float, list[str]]] = {}

        def _longest_path(node_id: str) -> tuple[float, list[str]]:
            if node_id in memo:
                return memo[node_id]
            node = self.nodes[node_id]
            dur = node.duration
            if not node.dependencies:
                res = (dur, [node_id])
                memo[node_id] = res
                return res

            best_parent_dur = 0.0
            best_parent_path: list[str] = []
            for dep in node.dependencies:
                if dep in self.nodes:
                    p_dur, p_path = _longest_path(dep)
                    if p_dur > best_parent_dur:
                        best_parent_dur = p_dur
                        best_parent_path = p_path

            res = (best_parent_dur + dur, best_parent_path + [node_id])
            memo[node_id] = res
            return res

        best_total = 0.0
        best_overall_path: list[str] = []
        for nid in self.nodes:
            tot, path = _longest_path(nid)
            if tot > best_total:
                best_total = tot
                best_overall_path = path

        self.critical_path = best_overall_path
        self.critical_path_duration = round(best_total, 4)
        return best_overall_path

    def calculate_bottlenecks(
        self, token_threshold: int = 10_000, duration_threshold: float = 5.0
    ) -> list[dict[str, Any]]:
        """Identify execution bottleneck nodes based on latency and token consumption."""
        bottlenecks = []
        for nid, node in self.nodes.items():
            reasons = []
            if node.duration >= duration_threshold:
                reasons.append(f"high_latency ({round(node.duration, 2)}s)")
            if node.tokens_used >= token_threshold:
                reasons.append(f"high_tokens ({node.tokens_used})")
            if node.status == "failed":
                reasons.append(f"node_failure: {node.error}")

            if reasons:
                bottlenecks.append(
                    {
                        "node_id": nid,
                        "role": node.role,
                        "duration": round(node.duration, 4),
                        "tokens_used": node.tokens_used,
                        "reasons": reasons,
                    }
                )
        self.bottlenecks = bottlenecks
        return bottlenecks

    def to_mermaid_graph(self) -> str:
        """Render Mermaid DAG topology annotated with execution status and metrics."""
        lines = ["graph TD"]
        for nid, node in self.nodes.items():
            dur_str = f"{round(node.duration, 2)}s"
            tok_str = f"{node.tokens_used}t"
            label = f"{node.id} [{node.role}]<br/>{node.status} | {dur_str} | {tok_str}"
            lines.append(f'    {nid}["{label}"]')
            for dep in node.dependencies:
                lines.append(f"    {dep} --> {nid}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "objective": self.objective,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": round(self.duration, 4),
            "total_tokens": self.total_tokens,
            "critical_path": self.critical_path,
            "critical_path_duration": self.critical_path_duration,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "waves": [w.to_dict() for w in self.waves],
            "bottlenecks": self.bottlenecks,
        }


@dataclass
class SwarmTaskResult:
    """Outcome of a complete Swarm DAG execution."""

    objective: str
    status: str  # "completed", "partial", "failed"
    run_id: str = ""
    final_synthesis: str = ""
    node_results: dict[str, Any] = field(default_factory=dict)
    total_tokens: int = 0
    consensus: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_tree: SwarmExecutionTree | None = None

    def to_dict(self) -> dict[str, Any]:
        res = {
            "run_id": self.run_id,
            "objective": self.objective,
            "status": self.status,
            "final_synthesis": self.final_synthesis,
            "node_results": self.node_results,
            "total_tokens": self.total_tokens,
            "consensus": self.consensus,
            "metadata": self.metadata,
        }
        if self.execution_tree is not None:
            res["execution_tree"] = self.execution_tree.to_dict()
        return res


__all__ = [
    "SwarmDAG",
    "SwarmExecutionTree",
    "SwarmNode",
    "SwarmNodeExecution",
    "SwarmTaskResult",
    "SwarmWaveMetrics",
]
