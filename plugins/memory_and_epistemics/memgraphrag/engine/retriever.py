"""Hybrid multi-layer graph retrieval combining TF-IDF seeds and Personalized PageRank diffusion."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any

from .nlp import _compute_tf_idf_vector, _cosine_similarity, _tokenize

if TYPE_CHECKING:
    from .memory import ThreeLayerMemory


def retrieve_hybrid(
    mem: ThreeLayerMemory,
    query: str,
    doc_frequencies: dict[str, int],
    num_to_retrieve: int = 5,
    damping: float = 0.5,
    passage_node_weight: float = 0.1,
) -> dict[str, Any]:
    """Execute hybrid multi-layer graph retrieval."""
    total_docs = max(1, len(mem.passage_layer))
    if not mem.passage_layer:
        return {"status": "ok", "query": query, "passages": [], "facts": [], "schemas": [], "retrieved_count": 0}

    query_tokens = _tokenize(query)
    q_vec = _compute_tf_idf_vector(query_tokens, doc_frequencies, total_docs)

    # 1. Compute Seed Relevance Scores on Passages & Facts
    passage_scores: dict[int, float] = {}
    for p in mem.passage_layer:
        p_tokens = _tokenize(p.content)
        p_vec = _compute_tf_idf_vector(p_tokens, doc_frequencies, total_docs)
        passage_scores[p.idx] = _cosine_similarity(q_vec, p_vec)

    fact_scores: dict[int, float] = {}
    for f in mem.fact_layer:
        f_text = f"{f.content[0]} {f.content[1]} {f.content[2]}"
        f_tokens = _tokenize(f_text)
        f_vec = _compute_tf_idf_vector(f_tokens, doc_frequencies, total_docs)
        fact_scores[f.idx] = _cosine_similarity(q_vec, f_vec)

    # 2. Graph Diffusion / Personalized PageRank Approximation
    final_passage_scores: dict[int, float] = defaultdict(float)
    for p_idx, base_score in passage_scores.items():
        final_passage_scores[p_idx] += (1.0 - damping) * base_score

    for f_idx, f_score in fact_scores.items():
        if f_score > 0:
            f_node = mem.fact_layer[f_idx]
            contrib = (damping * f_score) / max(1, len(f_node.passage_indices))
            for p_idx in f_node.passage_indices:
                final_passage_scores[p_idx] += contrib + (passage_node_weight * f_score)

    # 3. Rank Passages
    ranked_passages = sorted(final_passage_scores.items(), key=lambda x: x[1], reverse=True)[:num_to_retrieve]

    matched_passages = []
    associated_fact_indices: set[int] = set()
    for p_idx, score in ranked_passages:
        p_node = mem.passage_layer[p_idx]
        matched_passages.append({
            "idx": p_node.idx,
            "chunk_id": p_node.chunk_id,
            "content": p_node.content,
            "fact_indices": p_node.fact_indices,
            "score": round(score, 4),
        })
        associated_fact_indices.update(p_node.fact_indices)

    matched_facts = []
    associated_schema_indices: set[int] = set()
    for f_idx in sorted(associated_fact_indices):
        f_node = mem.fact_layer[f_idx]
        matched_facts.append({
            "idx": f_node.idx,
            "head": f_node.content[0],
            "relation": f_node.content[1],
            "tail": f_node.content[2],
            "frequency": f_node.frequency,
            "schema_idx": f_node.schema_idx,
            "passage_indices": f_node.passage_indices,
            "score": round(fact_scores.get(f_idx, 1.0), 4),
        })
        if f_node.schema_idx != -1:
            associated_schema_indices.add(f_node.schema_idx)

    matched_schemas = []
    for s_idx in sorted(associated_schema_indices):
        s_node = mem.schema_layer[s_idx]
        matched_schemas.append({
            "idx": s_node.idx,
            "head_type": s_node.content[0],
            "relation": s_node.content[1],
            "tail_type": s_node.content[2],
            "frequency": s_node.frequency,
            "fact_indices": s_node.fact_indices,
        })

    return {
        "status": "ok",
        "query": query,
        "passages": matched_passages,
        "facts": matched_facts,
        "schemas": matched_schemas,
        "retrieved_count": len(matched_passages),
    }
