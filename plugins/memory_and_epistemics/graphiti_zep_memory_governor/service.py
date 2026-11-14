"""Subprocess-isolated service adapter for Graphiti / Zep Temporal Memory Governor."""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys
from typing import Any

from harness.services.graphiti_zep_memory import (
    DEFAULT_MMR_LAMBDA,
    DEFAULT_RRF_RANK_CONST,
    BiTemporalEdgeNormalizationReport,
    CommunityAndOntologyReport,
    EntityDedupResolutionReport,
    GraphitiZepMemoryEngine,
    GraphitiZepMemoryProtocol,
    HybridRerankReport,
)


class DefaultGraphitiZepMemoryService(GraphitiZepMemoryProtocol):
    """Service adapter delegating to GraphitiZepMemoryEngine with Rule 14 subprocess pipe cleanup."""

    def __init__(self, root_dir: Path | None = None) -> None:
        self._root_dir = root_dir or Path(__file__).resolve().parents[3]
        self._engine = GraphitiZepMemoryEngine()

    def normalize_bitemporal_edges(
        self,
        fact: str,
        reference_time: str,
        valid_at: str | None = None,
        invalid_at: str | None = None,
        existing_edges: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        contradicted_ids: list[str] | tuple[str, ...] = (),
    ) -> BiTemporalEdgeNormalizationReport:
        return self._engine.normalize_bitemporal_edges(
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
        return self._engine.resolve_entities_and_endpoints(
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
        return self._engine.rerank_hybrid_results(
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
        return self._engine.cluster_communities_and_compile_ontology(
            neighbor_projection=neighbor_projection,
            episode_batches=episode_batches,
            entity_schemas=entity_schemas,
            edge_schemas=edge_schemas,
        )

    async def run_cli_subprocess(self, args: list[str], *, timeout: float = 30.0) -> dict[str, Any]:
        """Execute the skill CLI engine in a subprocess with explicit Rule 14 pipe closure."""
        script_path = (
            self._root_dir
            / ".agents"
            / "skills"
            / "graphiti-zep-memory-governor"
            / "scripts"
            / "graphiti_zep_memory_engine.py"
        )
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_data, stderr_data = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "returncode": proc.returncode,
                "stdout": stdout_data.decode("utf-8", errors="replace"),
                "stderr": stderr_data.decode("utf-8", errors="replace"),
            }
        finally:
            for pipe in (proc.stdin, proc.stdout, proc.stderr):
                close_fn = getattr(pipe, "close", None)
                if callable(close_fn):
                    try:
                        close_fn()
                    except Exception:
                        pass
