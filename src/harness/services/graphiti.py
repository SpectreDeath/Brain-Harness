"""Graphiti Temporal Knowledge Graph service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FactResult(BaseModel):
    """Represents an extracted or retrieved relational fact between entities."""

    edge_uuid: str = Field(..., description="Unique UUID for this fact relation")
    source_entity: str = Field(..., description="Source entity name or identifier")
    target_entity: str = Field(..., description="Target entity name or identifier")
    relation_name: str = Field(..., description="Name of the relationship (e.g. USES, IMPLEMENTS, PREFERS)")
    fact: str = Field(..., description="Natural language statement expressing the fact")
    valid_at: datetime = Field(..., description="Timestamp when the fact became valid")
    invalid_at: datetime | None = Field(default=None, description="Timestamp when superseded or invalidated, or None if currently valid")
    expired_at: datetime | None = Field(default=None, description="Optional TTL expiration timestamp")
    episodes: list[str] = Field(default_factory=list, description="List of contributing episode IDs")
    score: float = Field(default=1.0, description="Relevance score or search ranking score")


class EntityResult(BaseModel):
    """Represents a resolved semantic entity and its current state."""

    entity_uuid: str = Field(..., description="Unique UUID for the entity")
    name: str = Field(..., description="Canonical entity name")
    entity_type: str = Field(default="CONCEPT", description="Entity category or type")
    summary: str = Field(default="", description="Aggregated summary of facts known about this entity")
    attributes: dict[str, Any] = Field(default_factory=dict, description="Key-value attribute metadata")
    created_at: datetime = Field(default_factory=_utc_now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=_utc_now, description="Last update timestamp")
    relations: list[FactResult] = Field(default_factory=list, description="Incident relationship edges")


class EpisodeResult(BaseModel):
    """Result of episodic text or turn ingestion."""

    status: str = Field(default="ok", description="Status indicator (ok or error)")
    episode_uuid: str = Field(..., description="Assigned episode UUID")
    group_id: str = Field(default="default", description="Partition group ID")
    extracted_nodes_count: int = Field(default=0, description="Number of new or resolved entities")
    extracted_edges_count: int = Field(default=0, description="Number of new or updated fact edges")
    invalidated_edges_count: int = Field(default=0, description="Number of previous facts superseded")
    extracted_entities: list[str] = Field(default_factory=list, description="Names of extracted entities")


class SearchResult(BaseModel):
    """Result of tri-brid knowledge graph search."""

    status: str = Field(default="ok", description="Status indicator")
    query: str = Field(..., description="Original search query")
    group_id: str = Field(default="default", description="Partition group searched")
    results_count: int = Field(default=0, description="Total matching facts returned")
    facts: list[FactResult] = Field(default_factory=list, description="Ranked matching relationship facts")
    entities: list[EntityResult] = Field(default_factory=list, description="Matching entity nodes")


class GraphitiStatusResult(BaseModel):
    """Diagnostics and memory volume status."""

    status: str = Field(default="ok", description="Status indicator")
    backend: str = Field(default="in_process_temporal_graph", description="Active storage driver backend")
    group_id: str = Field(default="default", description="Partition group inspected")
    total_episodes: int = Field(default=0, description="Total ingested episodes")
    total_entities: int = Field(default=0, description="Total entity nodes")
    total_facts: int = Field(default=0, description="Total relationship edges")
    active_facts: int = Field(default=0, description="Currently valid facts (invalid_at is None)")
    invalidated_facts: int = Field(default=0, description="Superseded facts (invalid_at is not None)")


class GraphitiService(Protocol):
    """Protocol for the Graphiti Temporal Knowledge Graph service."""

    async def add_episode(
        self,
        content: str,
        group_id: str = "default",
        source_description: str | None = None,
    ) -> EpisodeResult:
        """Ingest episodic text/interaction and extract temporal entities and relations."""
        ...

    async def search(
        self,
        query: str,
        group_id: str = "default",
        limit: int = 5,
        include_invalidated: bool = False,
    ) -> SearchResult:
        """Execute tri-brid search (vector + BM25 + BFS) with cross-encoder reranking."""
        ...

    async def get_entity(
        self,
        name_or_uuid: str,
        group_id: str = "default",
    ) -> EntityResult | None:
        """Retrieve full entity node state, summaries, attributes, and relations."""
        ...

    async def invalidate_fact(
        self,
        edge_uuid: str,
        reason: str = "Contradicted by newer evidence",
    ) -> FactResult | None:
        """Mark a fact relation as superseded or invalid with timestamped record."""
        ...

    async def get_status(
        self,
        group_id: str = "default",
    ) -> GraphitiStatusResult:
        """Inspect knowledge graph memory statistics and driver backend health."""
        ...


GRAPHITI_MEMORY_KEY: ServiceKey[GraphitiService] = ServiceKey("service.graphiti_memory")
