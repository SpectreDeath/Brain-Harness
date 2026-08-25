"""MemGraphRAG Plugin & HarnessPlugin Service Implementation."""

from __future__ import annotations

from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.memgraphrag import (
    ConflictGroup,
    FactResult,
    MEMGRAPHRAG_MEMORY_KEY,
    MemGraphRAGConflictResult,
    MemGraphRAGIndexResult,
    MemGraphRAGQueryResult,
    MemGraphRAGRetrieveResult,
    MemGraphRAGService,
    MemGraphRAGSummaryResult,
    PassageResult,
    SchemaResult,
)

from .engine import MemGraphRAGEngine

logger = structlog.get_logger(__name__)

# Shared global engine instance for standalone tool execution
_ENGINE_INSTANCE = MemGraphRAGEngine()


def _get_engine() -> MemGraphRAGEngine:
    return _ENGINE_INSTANCE


def memgraphrag_index(
    docs: list[dict[str, Any]] | list[str],
    save_dir: str = "outputs/default",
    chunk_size: int = 256,
    chunk_overlap: int = 32,
    skip_conflict_resolution: bool = False,
) -> dict[str, Any]:
    """Ingest document passages, construct the 3-layer memory hierarchy, and build the retrieval graph."""
    engine = _get_engine()
    return engine.index(
        docs=docs,
        save_dir=save_dir,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        skip_conflict_resolution=skip_conflict_resolution,
    )


def memgraphrag_retrieve(
    query: str,
    save_dir: str = "outputs/default",
    num_to_retrieve: int = 5,
    damping: float = 0.5,
    passage_node_weight: float = 0.1,
) -> dict[str, Any]:
    """Execute hybrid multi-layer graph retrieval combining dense similarity and Personalized PageRank."""
    engine = _get_engine()
    return engine.retrieve(
        query=query,
        save_dir=save_dir,
        num_to_retrieve=num_to_retrieve,
        damping=damping,
        passage_node_weight=passage_node_weight,
    )


def memgraphrag_query(
    query: str,
    save_dir: str = "outputs/default",
    num_passages: int = 5,
) -> dict[str, Any]:
    """Synthesize an answer using retrieved multi-layer knowledge graph evidence."""
    engine = _get_engine()
    return engine.query(
        query=query,
        save_dir=save_dir,
        num_passages=num_passages,
    )


def memgraphrag_add_passage(
    chunk_id: str,
    content: str,
    extracted_triples: list[list[str]] | None = None,
    schema_tuple: list[str] | None = None,
    save_dir: str = "outputs/default",
) -> dict[str, Any]:
    """Incrementally inject a passage chunk and factual relation triples into the active memory graph."""
    engine = _get_engine()
    return engine.add_passage(
        chunk_id=chunk_id,
        content=content,
        extracted_triples=extracted_triples,
        schema_tuple=schema_tuple,
        save_dir=save_dir,
    )


def memgraphrag_get_memory_summary(
    save_dir: str = "outputs/default",
) -> dict[str, Any]:
    """Inspect statistical distribution and count metrics for schema, fact, and passage layers."""
    engine = _get_engine()
    return engine.get_summary(save_dir=save_dir)


def memgraphrag_detect_conflicts(
    save_dir: str = "outputs/default",
) -> dict[str, Any]:
    """Scan candidate facts for hard semantic contradictions with supporting passage evidence groups."""
    engine = _get_engine()
    return engine.detect_conflicts(save_dir=save_dir)


class MemGraphRAGPlugin(HarnessPlugin, MemGraphRAGService):
    """Harness Plugin implementing MemGraphRAGService and registering MEMGRAPHRAG_MEMORY_KEY."""

    name = "plugin.memgraphrag"
    version = "0.1.0"
    description = "Three-layer memory knowledge graph engine with conflict-aware graph construction and hybrid PPR retrieval"
    trusted = True

    def __init__(self) -> None:
        self._engine = _get_engine()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [MEMGRAPHRAG_MEMORY_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(MEMGRAPHRAG_MEMORY_KEY, self)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # MemGraphRAGService Protocol Implementation
    async def index(
        self,
        docs: list[dict[str, Any]] | list[str],
        save_dir: str = "outputs/default",
        chunk_size: int = 256,
        chunk_overlap: int = 32,
        skip_conflict_resolution: bool = False,
    ) -> MemGraphRAGIndexResult:
        res = memgraphrag_index(
            docs=docs,
            save_dir=save_dir,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            skip_conflict_resolution=skip_conflict_resolution,
        )
        return MemGraphRAGIndexResult(**res)

    async def retrieve(
        self,
        query: str,
        num_to_retrieve: int = 5,
        damping: float = 0.5,
        passage_node_weight: float = 0.1,
    ) -> MemGraphRAGRetrieveResult:
        res = memgraphrag_retrieve(
            query=query,
            num_to_retrieve=num_to_retrieve,
            damping=damping,
            passage_node_weight=passage_node_weight,
        )
        return MemGraphRAGRetrieveResult(
            status=res["status"],
            query=res["query"],
            passages=[PassageResult(**p) for p in res["passages"]],
            facts=[FactResult(**f) for f in res["facts"]],
            schemas=[SchemaResult(**s) for s in res["schemas"]],
            retrieved_count=res["retrieved_count"],
        )

    async def query(
        self,
        query: str,
        num_passages: int = 5,
    ) -> MemGraphRAGQueryResult:
        res = memgraphrag_query(query=query, num_passages=num_passages)
        return MemGraphRAGQueryResult(
            status=res["status"],
            query=res["query"],
            answer=res["answer"],
            retrieved_passages=[PassageResult(**p) for p in res["retrieved_passages"]],
            reasoning_steps=res["reasoning_steps"],
        )

    async def add_passage(
        self,
        chunk_id: str,
        content: str,
        extracted_triples: list[list[str]] | None = None,
        schema_tuple: list[str] | None = None,
    ) -> PassageResult:
        res = memgraphrag_add_passage(
            chunk_id=chunk_id,
            content=content,
            extracted_triples=extracted_triples,
            schema_tuple=schema_tuple,
        )
        return PassageResult(**res)

    async def get_summary(
        self,
        save_dir: str = "outputs/default",
    ) -> MemGraphRAGSummaryResult:
        res = memgraphrag_get_memory_summary(save_dir=save_dir)
        return MemGraphRAGSummaryResult(**res)

    async def detect_conflicts(
        self,
        save_dir: str = "outputs/default",
    ) -> MemGraphRAGConflictResult:
        res = memgraphrag_detect_conflicts(save_dir=save_dir)
        return MemGraphRAGConflictResult(
            status=res["status"],
            save_dir=res["save_dir"],
            conflicts_count=res["conflicts_count"],
            conflicts=[ConflictGroup(**c) for c in res["conflicts"]],
        )
