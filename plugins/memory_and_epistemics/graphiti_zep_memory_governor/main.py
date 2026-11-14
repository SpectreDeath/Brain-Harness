"""Graphiti / Zep Temporal Memory Governor Plugin — IoC provider and sandboxed entrypoints."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import sys
from typing import Any

import structlog

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_HARNESS_SRC = _REPO_ROOT / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext, ServiceKey  # noqa: E402
from harness.plugins.base import HarnessPlugin  # noqa: E402
from harness.services.graphiti_zep_memory import (  # noqa: E402
    DEFAULT_MMR_LAMBDA,
    DEFAULT_RRF_RANK_CONST,
    GRAPHITI_ZEP_MEMORY_KEY,
    BiTemporalEdgeNormalizationReport,
    CommunityAndOntologyReport,
    EntityDedupResolutionReport,
    GraphitiZepMemoryProtocol,
    HybridRerankReport,
)

try:
    from .service import DefaultGraphitiZepMemoryService
except ImportError:
    from service import DefaultGraphitiZepMemoryService  # type: ignore[no-redef]

logger = structlog.get_logger(__name__)


class GraphitiZepMemoryGovernorPlugin(HarnessPlugin, GraphitiZepMemoryProtocol):
    """HarnessPlugin providing GraphitiZepMemoryProtocol in the IoC container (Rule 45)."""

    name = "plugin.graphiti_zep_memory_governor"
    version = "1.0.0"
    description = (
        "Graphiti bi-temporal edge normalizer, MinHash/LSH entity deduplicator, "
        "RRF/MMR/hop-distance reranker, community clusterer, and Zep ontology compiler"
    )
    trusted = True

    def __init__(self) -> None:
        super().__init__()
        self._service = DefaultGraphitiZepMemoryService(root_dir=_REPO_ROOT)

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [GRAPHITI_ZEP_MEMORY_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(GRAPHITI_ZEP_MEMORY_KEY, self, provider=self.name)
        logger.info("GraphitiZepMemoryGovernorPlugin registered into IoC container")

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    def normalize_bitemporal_edges(
        self,
        fact: str,
        reference_time: str,
        valid_at: str | None = None,
        invalid_at: str | None = None,
        existing_edges: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        contradicted_ids: list[str] | tuple[str, ...] = (),
    ) -> BiTemporalEdgeNormalizationReport:
        return self._service.normalize_bitemporal_edges(
            fact=fact,
            reference_time=reference_time,
            valid_at=valid_at,
            invalid_at=invalid_at,
            existing_edges=existing_edges,
            contradicted_ids=contradicted_ids,
        )

    def resolve_entities_and_endpoints(
        self,
        extracted_entities: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        existing_entities: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        edge_endpoints: list[tuple[str, str]] | tuple[tuple[str, str], ...] = (),
        kept_edge_endpoints: list[tuple[str, str]] | tuple[tuple[str, str], ...] | None = None,
    ) -> EntityDedupResolutionReport:
        return self._service.resolve_entities_and_endpoints(
            extracted_entities=extracted_entities,
            existing_entities=existing_entities,
            edge_endpoints=edge_endpoints,
            kept_edge_endpoints=kept_edge_endpoints,
        )

    def rerank_hybrid_results(
        self,
        method: str,
        ranked_lists: list[list[str]] | tuple[list[str], ...] = (),
        query_vector: list[float] | tuple[float, ...] = (),
        candidate_vectors: dict[str, list[float]] | None = None,
        center_node_uuid: str | None = None,
        hop_distances: dict[str, float] | None = None,
        rank_const: int = DEFAULT_RRF_RANK_CONST,
        mmr_lambda: float = DEFAULT_MMR_LAMBDA,
        min_score: float = 0.0,
    ) -> HybridRerankReport:
        return self._service.rerank_hybrid_results(
            method=method,
            ranked_lists=ranked_lists,
            query_vector=query_vector,
            candidate_vectors=candidate_vectors,
            center_node_uuid=center_node_uuid,
            hop_distances=hop_distances,
            rank_const=rank_const,
            mmr_lambda=mmr_lambda,
            min_score=min_score,
        )

    def cluster_communities_and_compile_ontology(
        self,
        neighbor_projection: dict[str, list[dict[str, Any]]],
        episode_batches: list[dict[str, str]] | tuple[dict[str, str], ...] = (),
        entity_schemas: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        edge_schemas: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    ) -> CommunityAndOntologyReport:
        return self._service.cluster_communities_and_compile_ontology(
            neighbor_projection=neighbor_projection,
            episode_batches=episode_batches,
            entity_schemas=entity_schemas,
            edge_schemas=edge_schemas,
        )


plugin = GraphitiZepMemoryGovernorPlugin()


def zep_normalize_bitemporal_edges(
    fact: str,
    reference_time: str,
    valid_at: str | None = None,
    invalid_at: str | None = None,
    existing_edges: list[dict[str, Any]] | None = None,
    contradicted_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Clamp future assertion bounds, filter soft deadlines, and partition contradicted edges."""
    return asdict(
        plugin.normalize_bitemporal_edges(
            fact=fact,
            reference_time=reference_time,
            valid_at=valid_at,
            invalid_at=invalid_at,
            existing_edges=existing_edges or (),
            contradicted_ids=contradicted_ids or (),
        )
    )


def zep_resolve_entities_and_endpoints(
    extracted_entities: list[dict[str, Any]],
    existing_entities: list[dict[str, Any]] | None = None,
    edge_endpoints: list[tuple[str, str]] | None = None,
    kept_edge_endpoints: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    """Resolve entities via Shannon-entropy-gated MinHash/LSH and prune unreferenced endpoints."""
    return asdict(
        plugin.resolve_entities_and_endpoints(
            extracted_entities=extracted_entities,
            existing_entities=existing_entities or (),
            edge_endpoints=edge_endpoints or (),
            kept_edge_endpoints=kept_edge_endpoints,
        )
    )


def zep_rerank_hybrid_search(
    method: str,
    ranked_lists: list[list[str]] | None = None,
    query_vector: list[float] | None = None,
    candidate_vectors: dict[str, list[float]] | None = None,
    center_node_uuid: str | None = None,
    hop_distances: dict[str, float] | None = None,
    rank_const: int = DEFAULT_RRF_RANK_CONST,
    mmr_lambda: float = DEFAULT_MMR_LAMBDA,
    min_score: float = 0.0,
) -> dict[str, Any]:
    """Rerank search results via RRF, L2-normalized MMR, or shortest-hop distance."""
    return asdict(
        plugin.rerank_hybrid_results(
            method=method,
            ranked_lists=ranked_lists or (),
            query_vector=query_vector or (),
            candidate_vectors=candidate_vectors,
            center_node_uuid=center_node_uuid,
            hop_distances=hop_distances,
            rank_const=rank_const,
            mmr_lambda=mmr_lambda,
            min_score=min_score,
        )
    )


def zep_cluster_and_compile_ontology(
    neighbor_projection: dict[str, list[dict[str, Any]]],
    episode_batches: list[dict[str, str]] | None = None,
    entity_schemas: list[dict[str, Any]] | None = None,
    edge_schemas: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run weighted label propagation, validate group queue IDs, and compile Zep typed ontologies."""
    return asdict(
        plugin.cluster_communities_and_compile_ontology(
            neighbor_projection=neighbor_projection,
            episode_batches=episode_batches or (),
            entity_schemas=entity_schemas or (),
            edge_schemas=edge_schemas or (),
        )
    )
