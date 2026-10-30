"""Slotted and frozen data models for Knowledge Graph topology and exports (Rule 12)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class KnowledgeGraphNode:
    """Slotted immutable node representation in the knowledge graph."""

    id: str
    label: str
    node_kind: str = "ki"  # "ki", "skill", "plugin", "path", "source"
    category: str = "general"
    domain: str = "general"
    tags: tuple[str, ...] = ()
    status: str = "ACTIVE"
    retrieval_count: int = 0
    success_count: int = 0
    created_at: str = ""
    source_target: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True, frozen=True)
class KnowledgeGraphEdge:
    """Slotted immutable relationship edge connecting graph entities."""

    source: str
    target: str
    target_kind: str = "ki"  # "ki", "skill", "plugin", "path", "source"
    type: str = "same_domain"
    derived: bool = False
    confidence: float = 1.0
    shared_tags: tuple[str, ...] = ()
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True, frozen=True)
class KnowledgeGraphSummary:
    """Census metrics and coverage invariants for the knowledge graph."""

    total_nodes: int
    ki_nodes: int
    non_ki_nodes_by_kind: dict[str, int]
    total_edges: int
    edges_by_type: dict[str, int]
    derived_edge_count: int
    asserted_edge_count: int
    component_count: int
    largest_component_size: int
    isolated_ki_count: int
    untagged_ki_count: int
    uncategorized_ki_count: int
    excluded_mega_tags: tuple[str, ...] = ()
    date_coverage_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True, frozen=True)
class DerivedKnowledgeGraph:
    """Complete derived knowledge graph topology and summary."""

    nodes: tuple[KnowledgeGraphNode, ...]
    edges: tuple[KnowledgeGraphEdge, ...]
    summary: KnowledgeGraphSummary

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }

