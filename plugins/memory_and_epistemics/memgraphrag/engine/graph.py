"""Adjacency Graph Compilation and Multi-Layer Topology for MemGraphRAG."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .nlp import _infer_entity_type

if TYPE_CHECKING:
    from .memory import ThreeLayerMemory


def compile_memory_graph(mem: ThreeLayerMemory, save_dir: str) -> dict[str, Any]:
    """Compile Three-Layer Memory into an adjacency graph."""
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    # 1. Passage Nodes
    for p in mem.passage_layer:
        p_node_id = f"passage_{p.idx}"
        nodes[p_node_id] = {"type": "passage", "chunk_id": p.chunk_id, "content": p.content}

    # 2. Entity & Fact Nodes
    for f in mem.fact_layer:
        h, r, t = f.content
        h_node_id = f"entity_{h.lower()}"
        t_node_id = f"entity_{t.lower()}"

        if h_node_id not in nodes:
            nodes[h_node_id] = {"type": "entity", "name": h, "entity_type": _infer_entity_type(h)}
        if t_node_id not in nodes:
            nodes[t_node_id] = {"type": "entity", "name": t, "entity_type": _infer_entity_type(t)}

        # Fact edge
        edges.append({
            "source": h_node_id,
            "target": t_node_id,
            "relation": r,
            "fact_idx": f.idx,
            "weight": max(1.0, float(f.frequency)),
        })

        # Passage to Entity edges
        for p_idx in f.passage_indices:
            p_node_id = f"passage_{p_idx}"
            edges.append({"source": p_node_id, "target": h_node_id, "relation": "mentions", "weight": 1.0})
            edges.append({"source": p_node_id, "target": t_node_id, "relation": "mentions", "weight": 1.0})

    # 3. Schema Nodes
    for s in mem.schema_layer:
        s_node_id = f"schema_{s.idx}"
        nodes[s_node_id] = {
            "type": "schema",
            "ontology": s.content,
            "frequency": s.frequency,
        }

    return {
        "nodes": nodes,
        "edges": edges,
        "nodes_count": len(nodes),
        "edges_count": len(edges),
    }
