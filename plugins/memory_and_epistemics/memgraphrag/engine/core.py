"""Authoritative MemGraphRAGEngine Coordinator Class."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any
import structlog

from .conflicts import detect_conflicts_for_memory, resolve_conflicts_for_memory
from .graph import compile_memory_graph
from .memory import ThreeLayerMemory
from .models import ConflictGroupModel
from .nlp import _extract_triples_heuristic, _infer_entity_type, _tokenize
from .retriever import retrieve_hybrid
from .synthesis import (
    add_passage_chunk,
    calculate_memory_summary,
    synthesize_query_answer,
)

logger = structlog.get_logger(__name__)


class MemGraphRAGEngine:
    """Full-featured Three-Layer Memory and Hybrid Graph Retrieval Coordinator."""

    def __init__(self, default_save_dir: str = "outputs/default") -> None:
        self.default_save_dir = default_save_dir
        self._memories: dict[str, ThreeLayerMemory] = {}
        self._graphs: dict[str, dict[str, Any]] = {}
        self._doc_frequencies: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._conflict_registry: dict[str, list[ConflictGroupModel]] = defaultdict(list)

    def get_memory(self, save_dir: str | None = None) -> ThreeLayerMemory:
        """Retrieve memory instance for directory, loading from disk if present."""
        target = save_dir or self.default_save_dir
        if target not in self._memories:
            disk_path = Path(target) / "memory.json"
            if disk_path.exists():
                try:
                    with disk_path.open("r", encoding="utf-8") as f:
                        data = json.load(f)
                    self._memories[target] = ThreeLayerMemory.from_dict(data)
                except Exception as err:
                    logger.warning("failed_loading_memory_from_disk", path=str(disk_path), error=str(err))
                    self._memories[target] = ThreeLayerMemory()
            else:
                self._memories[target] = ThreeLayerMemory()
        return self._memories[target]

    def index(
        self,
        docs: list[dict[str, Any]] | list[str],
        save_dir: str = "outputs/default",
        chunk_size: int = 256,
        chunk_overlap: int = 32,
        skip_conflict_resolution: bool = False,
    ) -> dict[str, Any]:
        """Index documents into the three-layer memory hierarchy and compile graph."""
        mem = ThreeLayerMemory()
        doc_freq = self._doc_frequencies[save_dir]
        doc_freq.clear()

        # 1. Normalize documents into PassageNodes
        normalized_docs: list[dict[str, Any]] = []
        for i, item in enumerate(docs):
            if isinstance(item, str):
                normalized_docs.append({"idx": f"doc_{i}", "content": item})
            elif isinstance(item, dict):
                c_id = item.get("idx") or item.get("id") or item.get("chunk_id") or f"doc_{i}"
                txt = item.get("content") or item.get("passage") or item.get("text") or ""
                triples = item.get("extracted_triples") or item.get("triples") or []
                normalized_docs.append({"idx": str(c_id), "content": txt, "triples": triples})

        for d in normalized_docs:
            p_idx = mem.get_or_create_passage(d["idx"], d["content"])
            tokens = _tokenize(d["content"])
            for t in set(tokens):
                doc_freq[t] += 1

            triples = d.get("triples") or _extract_triples_heuristic(d["content"])
            for raw_t in triples:
                if isinstance(raw_t, (list, tuple)) and len(raw_t) == 3:
                    h, r, t = str(raw_t[0]), str(raw_t[1]), str(raw_t[2])
                    f_idx = mem.get_or_create_fact((h, r, t))
                    mem.link_passage_and_fact(p_idx, f_idx)

                    h_type = _infer_entity_type(h)
                    t_type = _infer_entity_type(t)
                    s_idx = mem.get_or_create_schema((h_type, r, t_type))
                    mem.link_fact_and_schema(f_idx, s_idx)

        # 2. Detect and resolve conflicts
        conflicts = detect_conflicts_for_memory(mem)
        self._conflict_registry[save_dir] = conflicts
        resolved_count = 0
        if not skip_conflict_resolution and conflicts:
            resolved_count = resolve_conflicts_for_memory(mem, conflicts)

        # 3. Build Compiled Memory Graph
        graph_stats = compile_memory_graph(mem, save_dir)
        self._graphs[save_dir] = graph_stats
        self._memories[save_dir] = mem

        # Persist to disk if path exists or can be created
        try:
            out_p = Path(save_dir)
            out_p.mkdir(parents=True, exist_ok=True)
            with (out_p / "memory.json").open("w", encoding="utf-8") as f:
                json.dump(mem.to_dict(), f, indent=2)
        except Exception as err:
            logger.warning("could_not_save_memory_disk", path=save_dir, error=str(err))

        return {
            "status": "ok",
            "save_dir": save_dir,
            "passages_count": len(mem.passage_layer),
            "facts_count": len(mem.fact_layer),
            "schemas_count": len(mem.schema_layer),
            "conflicts_detected": len(conflicts),
            "conflicts_resolved": resolved_count,
            "graph_nodes_count": graph_stats.get("nodes_count", 0),
            "graph_edges_count": graph_stats.get("edges_count", 0),
        }

    def retrieve(
        self,
        query: str,
        save_dir: str = "outputs/default",
        num_to_retrieve: int = 5,
        damping: float = 0.5,
        passage_node_weight: float = 0.1,
    ) -> dict[str, Any]:
        """Execute hybrid multi-layer graph retrieval combining TF-IDF and PageRank diffusion."""
        mem = self.get_memory(save_dir)
        doc_freq = self._doc_frequencies[save_dir]
        return retrieve_hybrid(
            mem=mem,
            query=query,
            doc_frequencies=doc_freq,
            num_to_retrieve=num_to_retrieve,
            damping=damping,
            passage_node_weight=passage_node_weight,
        )

    def query(
        self,
        query: str,
        save_dir: str = "outputs/default",
        num_passages: int = 5,
    ) -> dict[str, Any]:
        """Synthesize an answer using multi-layer graph evidence."""
        ret = self.retrieve(query, save_dir=save_dir, num_to_retrieve=num_passages)
        return synthesize_query_answer(query=query, retrieval_result=ret)

    def add_passage(
        self,
        chunk_id: str,
        content: str,
        extracted_triples: list[list[str]] | None = None,
        schema_tuple: list[str] | None = None,
        save_dir: str = "outputs/default",
    ) -> dict[str, Any]:
        """Incrementally inject a passage chunk and factual triples into memory."""
        mem = self.get_memory(save_dir)
        doc_freq = self._doc_frequencies[save_dir]
        result = add_passage_chunk(
            mem=mem,
            chunk_id=chunk_id,
            content=content,
            doc_frequencies=doc_freq,
            extracted_triples=extracted_triples,
            schema_tuple=schema_tuple,
        )
        self._graphs[save_dir] = compile_memory_graph(mem, save_dir)
        return result

    def get_summary(self, save_dir: str = "outputs/default") -> dict[str, Any]:
        """Inspect summary distribution and count metrics for 3-layer memory."""
        mem = self.get_memory(save_dir)
        graph = self._graphs.get(save_dir, {"nodes_count": 0, "edges_count": 0})
        return calculate_memory_summary(mem, graph, save_dir)

    def detect_conflicts(self, save_dir: str = "outputs/default") -> dict[str, Any]:
        """Detect conflicts in active memory or return existing resolved conflict registry."""
        if save_dir in self._conflict_registry and self._conflict_registry[save_dir]:
            conflicts = self._conflict_registry[save_dir]
        else:
            mem = self.get_memory(save_dir)
            conflicts = detect_conflicts_for_memory(mem)
            self._conflict_registry[save_dir] = conflicts
        return {
            "status": "ok",
            "save_dir": save_dir,
            "conflicts_count": len(conflicts),
            "conflicts": [c.model_dump() for c in conflicts],
        }
