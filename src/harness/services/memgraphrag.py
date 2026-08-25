"""MemGraphRAG Three-Layer Memory Graph service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SchemaResult(BaseModel):
    """Ontology schema node (head_type, relation, tail_type)."""

    idx: int = Field(..., description="Unique schema index")
    head_type: str = Field(..., description="Subject ontology entity type")
    relation: str = Field(..., description="Relation predicate")
    tail_type: str = Field(..., description="Object ontology entity type")
    frequency: int = Field(default=1, description="Number of facts governed by this schema")
    fact_indices: list[int] = Field(default_factory=list, description="Associated lower-level fact indices")


class FactResult(BaseModel):
    """Relational fact triple (head, relation, tail)."""

    idx: int = Field(..., description="Unique fact index")
    head: str = Field(..., description="Subject entity name")
    relation: str = Field(..., description="Relation predicate")
    tail: str = Field(..., description="Object entity name")
    frequency: int = Field(default=1, description="Number of supporting passage chunks")
    schema_idx: int = Field(default=-1, description="Governing upper-level ontology schema index")
    passage_indices: list[int] = Field(default_factory=list, description="Supporting passage indices")
    score: float = Field(default=1.0, description="Relevance or retrieval ranking score")


class PassageResult(BaseModel):
    """Source text passage / chunk supporting facts."""

    idx: int = Field(..., description="Unique passage index")
    chunk_id: str = Field(..., description="Unique document chunk identifier")
    content: str = Field(..., description="Text content of the passage chunk")
    fact_indices: list[int] = Field(default_factory=list, description="Extracted factual triple indices")
    score: float = Field(default=0.0, description="Retrieval relevance score")


class MemGraphRAGIndexResult(BaseModel):
    """Result of memory indexing operation."""

    status: str = Field(default="ok", description="Status code")
    save_dir: str = Field(default="outputs/default", description="Persistence storage directory")
    passages_count: int = Field(default=0, description="Total indexed passage nodes")
    facts_count: int = Field(default=0, description="Total extracted fact nodes")
    schemas_count: int = Field(default=0, description="Total abstracted ontology schema nodes")
    conflicts_detected: int = Field(default=0, description="Total detected factual conflict groups")
    conflicts_resolved: int = Field(default=0, description="Total resolved conflicts")
    graph_nodes_count: int = Field(default=0, description="Nodes in compiled memory graph")
    graph_edges_count: int = Field(default=0, description="Edges in compiled memory graph")


class MemGraphRAGRetrieveResult(BaseModel):
    """Result of hybrid multi-layer graph retrieval."""

    status: str = Field(default="ok", description="Status indicator")
    query: str = Field(..., description="Natural language search query")
    passages: list[PassageResult] = Field(default_factory=list, description="Top ranked evidence passages")
    facts: list[FactResult] = Field(default_factory=list, description="Associated fact relation triples")
    schemas: list[SchemaResult] = Field(default_factory=list, description="Associated ontology schemas")
    retrieved_count: int = Field(default=0, description="Total retrieved items")


class MemGraphRAGQueryResult(BaseModel):
    """Result of RAG Question Answering."""

    status: str = Field(default="ok", description="Status indicator")
    query: str = Field(..., description="Input user question")
    answer: str = Field(..., description="Synthesized answer from graph memory")
    retrieved_passages: list[PassageResult] = Field(default_factory=list, description="Evidence passages used")
    reasoning_steps: list[str] = Field(default_factory=list, description="Reasoning and retrieval trajectory")


class MemGraphRAGSummaryResult(BaseModel):
    """Statistical summary of three-layer memory."""

    status: str = Field(default="ok", description="Status indicator")
    save_dir: str = Field(default="outputs/default", description="Partition directory")
    num_schemas: int = Field(default=0, description="Schema count")
    num_facts: int = Field(default=0, description="Fact count")
    num_passages: int = Field(default=0, description="Passage count")
    num_graph_nodes: int = Field(default=0, description="Graph nodes count")
    num_graph_edges: int = Field(default=0, description="Graph edges count")
    avg_facts_per_schema: float = Field(default=0.0, description="Average facts per schema")
    avg_passages_per_fact: float = Field(default=0.0, description="Average passages per fact")


class ConflictGroup(BaseModel):
    """Group of conflicting facts sharing the same subject and relation with contradictory objects."""

    group_id: str = Field(..., description="Unique conflict group ID")
    head: str = Field(..., description="Conflicting subject entity")
    relation: str = Field(..., description="Conflicting relation")
    conflicting_tails: list[str] = Field(default_factory=list, description="Contradictory tail entities")
    fact_indices: list[int] = Field(default_factory=list, description="Fact node indices involved")
    supporting_passage_indices: list[int] = Field(default_factory=list, description="Supporting passage indices")
    resolution_status: str = Field(default="pending", description="Resolution status (pending, resolved, discarded)")
    resolved_tail: str | None = Field(default=None, description="Winning or merged tail entity after resolution")


class MemGraphRAGConflictResult(BaseModel):
    """Result of conflict detection inspection."""

    status: str = Field(default="ok", description="Status indicator")
    save_dir: str = Field(default="outputs/default", description="Target partition")
    conflicts_count: int = Field(default=0, description="Number of detected conflict groups")
    conflicts: list[ConflictGroup] = Field(default_factory=list, description="Detected conflict groups")


@runtime_checkable
class MemGraphRAGService(Protocol):
    """Protocol for the MemGraphRAG Knowledge Graph Memory Service."""

    async def index(
        self,
        docs: list[dict[str, Any]] | list[str],
        save_dir: str = "outputs/default",
        chunk_size: int = 256,
        chunk_overlap: int = 32,
        skip_conflict_resolution: bool = False,
    ) -> MemGraphRAGIndexResult:
        """Construct 3-layer memory hierarchy, extract schemas, resolve conflicts, and compile graph."""
        ...

    async def retrieve(
        self,
        query: str,
        num_to_retrieve: int = 5,
        damping: float = 0.5,
        passage_node_weight: float = 0.1,
    ) -> MemGraphRAGRetrieveResult:
        """Execute hybrid multi-layer graph retrieval (dense vector + Personalized PageRank)."""
        ...

    async def query(
        self,
        query: str,
        num_passages: int = 5,
    ) -> MemGraphRAGQueryResult:
        """Synthesize answer using multi-layer graph retrieval evidence."""
        ...

    async def add_passage(
        self,
        chunk_id: str,
        content: str,
        extracted_triples: list[list[str]] | None = None,
        schema_tuple: list[str] | None = None,
    ) -> PassageResult:
        """Incrementally inject a passage chunk and factual triples into memory."""
        ...

    async def get_summary(
        self,
        save_dir: str = "outputs/default",
    ) -> MemGraphRAGSummaryResult:
        """Inspect 3-layer memory counts and graph topology metrics."""
        ...

    async def detect_conflicts(
        self,
        save_dir: str = "outputs/default",
    ) -> MemGraphRAGConflictResult:
        """Detect and group contradictory facts with supporting passage evidence."""
        ...


MEMGRAPHRAG_MEMORY_KEY: ServiceKey[MemGraphRAGService] = ServiceKey("service.memgraphrag")
