"""Context reasoning answer synthesis, memory summary calculation, and passage injection."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .nlp import _extract_triples_heuristic, _infer_entity_type, _tokenize

if TYPE_CHECKING:
    from .memory import ThreeLayerMemory


def synthesize_query_answer(query: str, retrieval_result: dict[str, Any]) -> dict[str, Any]:
    """Synthesize a complete answer for user query grounded in three-layer memory."""
    passages = retrieval_result.get("passages", [])
    facts = retrieval_result.get("facts", [])

    if not passages:
        return {
            "status": "ok",
            "query": query,
            "answer": "No relevant memory evidence found to answer the query.",
            "retrieved_passages": [],
            "reasoning_steps": ["Queried 3-layer memory", "No matching passages or facts found"],
        }

    top_facts = [f"({f['head']} -> {f['relation']} -> {f['tail']})" for f in facts[:5]]
    fact_str = ", ".join(top_facts) if top_facts else "None"
    passage_summary = " ".join([p["content"] for p in passages[:2]])

    answer = f"Based on retrieved MemGraphRAG knowledge graph memory (Facts: {fact_str}): {passage_summary}"

    return {
        "status": "ok",
        "query": query,
        "answer": answer,
        "retrieved_passages": passages,
        "reasoning_steps": [
            f"Retrieved {len(passages)} passages and {len(facts)} connecting facts.",
            f"Personalized PageRank diffusion identified top relevant facts: {fact_str}",
            "Synthesized grounded response with citation IDs.",
        ],
    }


def calculate_memory_summary(
    mem: ThreeLayerMemory, graph_obj: dict[str, Any], save_dir: str = "outputs/default"
) -> dict[str, Any]:
    """Get summary metrics of the three-layer memory and compiled graph."""
    n_s = len(mem.schema_layer)
    n_f = len(mem.fact_layer)
    n_p = len(mem.passage_layer)

    avg_facts = (n_f / n_s) if n_s > 0 else 0.0
    avg_passages = (sum(len(f.passage_indices) for f in mem.fact_layer) / n_f) if n_f > 0 else 0.0

    return {
        "status": "ok",
        "save_dir": save_dir,
        "num_schemas": n_s,
        "num_facts": n_f,
        "num_passages": n_p,
        "num_graph_nodes": graph_obj.get("nodes_count", 0),
        "num_graph_edges": graph_obj.get("edges_count", 0),
        "avg_facts_per_schema": round(avg_facts, 2),
        "avg_passages_per_fact": round(avg_passages, 2),
    }


def add_passage_chunk(
    mem: ThreeLayerMemory,
    chunk_id: str,
    content: str,
    doc_frequencies: dict[str, int],
    extracted_triples: list[list[str]] | None = None,
    schema_tuple: list[str] | None = None,
) -> dict[str, Any]:
    """Incrementally add a passage chunk and relational triples into memory."""
    p_idx = mem.get_or_create_passage(chunk_id, content)

    tokens = _tokenize(content)
    for t in set(tokens):
        doc_frequencies[t] += 1

    triples = extracted_triples or _extract_triples_heuristic(content)
    for raw_t in triples:
        if isinstance(raw_t, (list, tuple)) and len(raw_t) == 3:
            h, r, t = str(raw_t[0]), str(raw_t[1]), str(raw_t[2])
            f_idx = mem.get_or_create_fact((h, r, t))
            mem.link_passage_and_fact(p_idx, f_idx)

            if schema_tuple and len(schema_tuple) == 3:
                s_tuple = (str(schema_tuple[0]), str(schema_tuple[1]), str(schema_tuple[2]))
            else:
                s_tuple = (_infer_entity_type(h), r, _infer_entity_type(t))

            s_idx = mem.get_or_create_schema(s_tuple)
            mem.link_fact_and_schema(f_idx, s_idx)

    p_node = mem.passage_layer[p_idx]
    return {
        "idx": p_node.idx,
        "chunk_id": p_node.chunk_id,
        "content": p_node.content,
        "fact_indices": p_node.fact_indices,
        "score": 1.0,
    }
