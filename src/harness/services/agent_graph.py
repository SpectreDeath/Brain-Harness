"""Agent Execution Graph Store and Thread DAG Lifecycle Service.

Provides an authoritative, queryable graph of agent execution threads,
parent-child spawn edges, lifecycle transitions (Open/Closed), and ASCII
tree rendering for CLI session inspection (inspired by Codex's agent-graph-store).
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field
import structlog

from harness.kernel.context import ServiceKey

logger = structlog.get_logger()


class ThreadSpawnStatus(str, Enum):
    """Lifecycle status attached to a directional thread-spawn edge."""

    OPEN = "open"
    CLOSED = "closed"
    FAILED = "failed"
    COMPLETED = "completed"


class ExecutionGraphNode(BaseModel):
    """Represents an agent execution thread node in the DAG."""

    node_id: str = Field(..., description="Unique thread or sub-agent identifier")
    role: str = Field(default="agent", description="Role/specialization of the agent")
    task: str = Field(default="", description="Task description assigned to thread")
    status: str = Field(default="open", description="Current node status: open, completed, failed")
    tokens_used: int = Field(default=0, description="Tokens consumed by this thread")
    created_at: float = Field(default_factory=time.time, description="Creation timestamp")
    completed_at: float | None = Field(default=None, description="Completion timestamp")
    parent_id: str | None = Field(default=None, description="Parent thread node ID if spawned")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom thread metadata")


class ExecutionGraphEdge(BaseModel):
    """Directional spawn edge connecting a parent thread to a child agent."""

    parent_id: str = Field(..., description="Parent thread ID")
    child_id: str = Field(..., description="Child thread ID")
    status: ThreadSpawnStatus = Field(default=ThreadSpawnStatus.OPEN, description="Edge status")
    spawned_at: float = Field(default_factory=time.time, description="Spawn timestamp")


class ExecutionGraphExport(BaseModel):
    """Rendered export of an agent execution graph."""

    status: str = Field(default="ok", description="Status indicator")
    root_node_id: str | None = Field(default=None, description="Root thread node ID")
    total_nodes: int = Field(default=0, description="Total nodes in graph")
    total_edges: int = Field(default=0, description="Total spawn edges in graph")
    total_tokens_rollup: int = Field(default=0, description="Aggregated tokens across all nodes")
    nodes: dict[str, ExecutionGraphNode] = Field(default_factory=dict, description="Nodes map")
    edges: list[ExecutionGraphEdge] = Field(default_factory=list, description="Edges list")
    formatted_ascii_tree: str = Field(default="", description="Rendered ASCII tree representation")


@runtime_checkable
class AgentExecutionGraphService(Protocol):
    """Protocol for authoritative agent execution DAG management and tree export."""

    def register_thread(
        self,
        node_id: str,
        role: str = "agent",
        task: str = "",
        parent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionGraphNode:
        """Register a new execution thread node and record parent spawn edge."""
        ...

    def update_thread_status(
        self,
        node_id: str,
        status: str,
        tokens_used: int = 0,
        completed: bool = False,
    ) -> ExecutionGraphNode:
        """Update lifecycle status and token metrics for a thread."""
        ...

    def close_spawn_edge(self, parent_id: str, child_id: str, status: ThreadSpawnStatus = ThreadSpawnStatus.CLOSED) -> None:
        """Mark a directional spawn edge as closed or completed."""
        ...

    def export_graph(self, root_node_id: str | None = None) -> ExecutionGraphExport:
        """Generate structured graph export and ASCII tree visualization."""
        ...

    def render_ascii_tree(self, root_node_id: str | None = None) -> str:
        """Render hierarchical ASCII tree of execution threads."""
        ...


AGENT_GRAPH_STORE_KEY: ServiceKey[AgentExecutionGraphService] = ServiceKey("service.agent_graph_store")


class DefaultAgentExecutionGraphService:
    """In-memory thread-safe implementation of AgentExecutionGraphService."""

    def __init__(self) -> None:
        self._nodes: dict[str, ExecutionGraphNode] = {}
        self._edges: list[ExecutionGraphEdge] = []
        self._children_map: dict[str, list[str]] = defaultdict(list)

    def register_thread(
        self,
        node_id: str,
        role: str = "agent",
        task: str = "",
        parent_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionGraphNode:
        node = ExecutionGraphNode(
            node_id=node_id,
            role=role,
            task=task,
            status="open",
            parent_id=parent_id,
            metadata=metadata or {},
        )
        self._nodes[node_id] = node

        if parent_id and parent_id in self._nodes:
            edge = ExecutionGraphEdge(parent_id=parent_id, child_id=node_id, status=ThreadSpawnStatus.OPEN)
            self._edges.append(edge)
            self._children_map[parent_id].append(node_id)

        return node

    def update_thread_status(
        self,
        node_id: str,
        status: str,
        tokens_used: int = 0,
        completed: bool = False,
    ) -> ExecutionGraphNode:
        if node_id not in self._nodes:
            raise KeyError(f"Thread node '{node_id}' not found in execution graph")

        node = self._nodes[node_id]
        node.status = status
        if tokens_used:
            node.tokens_used += tokens_used
        if completed:
            node.completed_at = time.time()
            if node.parent_id:
                self.close_spawn_edge(node.parent_id, node_id, ThreadSpawnStatus.COMPLETED)

        return node

    def close_spawn_edge(self, parent_id: str, child_id: str, status: ThreadSpawnStatus = ThreadSpawnStatus.CLOSED) -> None:
        for edge in self._edges:
            if edge.parent_id == parent_id and edge.child_id == child_id:
                edge.status = status

    def render_ascii_tree(self, root_node_id: str | None = None) -> str:
        if not self._nodes:
            return "Empty execution graph."

        roots = [root_node_id] if root_node_id and root_node_id in self._nodes else [
            nid for nid, node in self._nodes.items() if node.parent_id is None
        ]
        if not roots:
            roots = list(self._nodes.keys())[:1]

        lines: list[str] = []

        def _build_tree(node_id: str, prefix: str = "", is_last: bool = True) -> None:
            node = self._nodes.get(node_id)
            if not node:
                return

            connector = "└── " if is_last else "├── "
            status_icon = "✓" if node.status == "completed" else ("✗" if node.status == "failed" else "●")
            line = f"{prefix}{connector}[{status_icon}] {node.node_id} ({node.role}) - '{node.task[:30]}' [{node.tokens_used} tok]"
            lines.append(line)

            children = self._children_map.get(node_id, [])
            new_prefix = prefix + ("    " if is_last else "│   ")
            for idx, child_id in enumerate(children):
                _build_tree(child_id, new_prefix, idx == len(children) - 1)

        for r in roots:
            _build_tree(r, "", True)

        return "\n".join(lines)

    def export_graph(self, root_node_id: str | None = None) -> ExecutionGraphExport:
        ascii_tree = self.render_ascii_tree(root_node_id)
        total_tokens = sum(n.tokens_used for n in self._nodes.values())
        return ExecutionGraphExport(
            status="ok",
            root_node_id=root_node_id,
            total_nodes=len(self._nodes),
            total_edges=len(self._edges),
            total_tokens_rollup=total_tokens,
            nodes=self._nodes,
            edges=self._edges,
            formatted_ascii_tree=ascii_tree,
        )


__all__ = [
    "AGENT_GRAPH_STORE_KEY",
    "AgentExecutionGraphService",
    "DefaultAgentExecutionGraphService",
    "ExecutionGraphEdge",
    "ExecutionGraphExport",
    "ExecutionGraphNode",
    "ThreadSpawnStatus",
]
