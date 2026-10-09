"""MemGraphRAG Engine modular subpackage facade."""

from __future__ import annotations

from .conflicts import detect_conflicts_for_memory, resolve_conflicts_for_memory
from .core import MemGraphRAGEngine
from .graph import compile_memory_graph
from .memory import ThreeLayerMemory
from .models import ConflictGroupModel, FactNode, PassageNode, SchemaNode
from .nlp import (
    _compute_tf_idf_vector,
    _cosine_similarity,
    _extract_triples_heuristic,
    _infer_entity_type,
    _tokenize,
)
from .resolvers import resolve_memgraphrag_engine
from .retriever import retrieve_hybrid
from .synthesis import (
    add_passage_chunk,
    calculate_memory_summary,
    synthesize_query_answer,
)

__all__ = [
    "ConflictGroupModel",
    "FactNode",
    "MemGraphRAGEngine",
    "PassageNode",
    "SchemaNode",
    "ThreeLayerMemory",
    "_compute_tf_idf_vector",
    "_cosine_similarity",
    "_extract_triples_heuristic",
    "_infer_entity_type",
    "_tokenize",
    "add_passage_chunk",
    "calculate_memory_summary",
    "compile_memory_graph",
    "detect_conflicts_for_memory",
    "resolve_conflicts_for_memory",
    "resolve_memgraphrag_engine",
    "retrieve_hybrid",
    "synthesize_query_answer",
]
