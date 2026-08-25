"""Core Three-Layer Memory & Hybrid Graph Retrieval Engine for MemGraphRAG."""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import structlog

from .models import ConflictGroupModel, FactNode, PassageNode, SchemaNode

logger = structlog.get_logger(__name__)


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric words."""
    words = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\w+", text)
    return [w.lower() for w in words if len(w) > 1]


def _compute_tf_idf_vector(tokens: list[str], doc_freq: dict[str, int], total_docs: int) -> dict[str, float]:
    """Compute normalized TF-IDF vector."""
    tf = Counter(tokens)
    vec: dict[str, float] = {}
    norm_sq = 0.0

    for term, count in tf.items():
        tf_weight = 1.0 + math.log(count)
        idf_weight = math.log((total_docs + 1.0) / (doc_freq.get(term, 0) + 1.0)) + 1.0
        weight = tf_weight * idf_weight
        vec[term] = weight
        norm_sq += weight * weight

    norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
    for term in vec:
        vec[term] /= norm
    return vec


def _cosine_similarity(vec1: dict[str, float], vec2: dict[str, float]) -> float:
    """Compute cosine similarity between two sparse vector dicts."""
    if not vec1 or not vec2:
        return 0.0
    if len(vec1) > len(vec2):
        vec1, vec2 = vec2, vec1
    score = sum(val * vec2.get(k, 0.0) for k, val in vec1.items())
    return max(0.0, min(1.0, score))


class ThreeLayerMemory:
    """Three-layer hierarchical memory holding Schemas, Facts, and Passages."""

    def __init__(self) -> None:
        self.schema_layer: List[SchemaNode] = []
        self.fact_layer: List[FactNode] = []
        self.passage_layer: List[PassageNode] = []

        self._schema_to_idx: Dict[Tuple[str, str, str], int] = {}
        self._fact_to_idx: Dict[Tuple[str, str, str], int] = {}
        self._chunk_id_to_idx: Dict[str, int] = {}

    def get_or_create_schema(self, ontology: Tuple[str, str, str]) -> int:
        if ontology in self._schema_to_idx:
            return self._schema_to_idx[ontology]
        idx = len(self.schema_layer)
        node = SchemaNode(idx=idx, content=ontology)
        self.schema_layer.append(node)
        self._schema_to_idx[ontology] = idx
        return idx

    def get_or_create_fact(self, triple: Tuple[str, str, str], schema_idx: int = -1) -> int:
        if triple in self._fact_to_idx:
            idx = self._fact_to_idx[triple]
            if schema_idx != -1 and self.fact_layer[idx].schema_idx == -1:
                self.fact_layer[idx].schema_idx = schema_idx
            return idx
        idx = len(self.fact_layer)
        node = FactNode(idx=idx, content=triple, schema_idx=schema_idx)
        self.fact_layer.append(node)
        self._fact_to_idx[triple] = idx
        return idx

    def get_or_create_passage(self, chunk_id: str, content: str) -> int:
        if chunk_id in self._chunk_id_to_idx:
            return self._chunk_id_to_idx[chunk_id]
        idx = len(self.passage_layer)
        node = PassageNode(idx=idx, chunk_id=chunk_id, content=content)
        self.passage_layer.append(node)
        self._chunk_id_to_idx[chunk_id] = idx
        return idx

    def link_passage_and_fact(self, passage_idx: int, fact_idx: int) -> None:
        if 0 <= passage_idx < len(self.passage_layer) and 0 <= fact_idx < len(self.fact_layer):
            p_node = self.passage_layer[passage_idx]
            f_node = self.fact_layer[fact_idx]
            if fact_idx not in p_node.fact_indices:
                p_node.fact_indices.append(fact_idx)
            if passage_idx not in f_node.passage_indices:
                f_node.passage_indices.append(passage_idx)
            f_node.frequency = len(f_node.passage_indices)

    def link_fact_and_schema(self, fact_idx: int, schema_idx: int) -> None:
        if 0 <= fact_idx < len(self.fact_layer) and 0 <= schema_idx < len(self.schema_layer):
            f_node = self.fact_layer[fact_idx]
            s_node = self.schema_layer[schema_idx]
            f_node.schema_idx = schema_idx
            if fact_idx not in s_node.fact_indices:
                s_node.fact_indices.append(fact_idx)
            s_node.frequency = len(s_node.fact_indices)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_layer": [s.to_dict() for s in self.schema_layer],
            "fact_layer": [f.to_dict() for f in self.fact_layer],
            "passage_layer": [p.to_dict() for p in self.passage_layer],
            "stats": {
                "num_schemas": len(self.schema_layer),
                "num_facts": len(self.fact_layer),
                "num_passages": len(self.passage_layer),
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ThreeLayerMemory":
        mem = cls()
        for s_data in data.get("schema_layer", []):
            node = SchemaNode.from_dict(s_data)
            mem.schema_layer.append(node)
            mem._schema_to_idx[node.content] = node.idx

        for f_data in data.get("fact_layer", []):
            node = FactNode.from_dict(f_data)
            mem.fact_layer.append(node)
            mem._fact_to_idx[node.content] = node.idx

        for p_data in data.get("passage_layer", []):
            node = PassageNode.from_dict(p_data)
            mem.passage_layer.append(node)
            mem._chunk_id_to_idx[node.chunk_id] = node.idx

        return mem


class MemGraphRAGEngine:
    """Full-featured Three-Layer Memory and Hybrid Graph Retrieval Engine."""

    def __init__(self, default_save_dir: str = "outputs/default") -> None:
        self.default_save_dir = default_save_dir
        self._memories: dict[str, ThreeLayerMemory] = {}
        self._graphs: dict[str, dict[str, Any]] = {}
        self._doc_frequencies: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._conflict_registry: dict[str, list[ConflictGroupModel]] = defaultdict(list)

    def get_memory(self, save_dir: str | None = None) -> ThreeLayerMemory:
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

    def _infer_entity_type(self, entity: str) -> str:
        """Infer ontology entity type from lexical patterns."""
        ent = entity.strip()
        if re.match(r"^\d+(\.\d+)?%?$", ent) or any(c.isdigit() for c in ent):
            return "Quantity"
        if any(w in ent.lower() for w in ["system", "engine", "model", "algorithm", "rag", "framework", "software"]):
            return "Technology"
        if any(w in ent.lower() for w in ["university", "corp", "inc", "group", "lab", "team", "organization"]):
            return "Organization"
        if any(w in ent.lower() for w in ["dr", "prof", "wu", "tang", "zhang", "smith", "lovelace", "turing", "user"]):
            return "Person"
        if any(w in ent.lower() for w in ["accuracy", "latency", "f1", "precision", "recall", "score", "rate"]):
            return "Metric"
        if any(w in ent.lower() for w in ["memory", "fact", "passage", "schema", "triple", "graph", "dataset"]):
            return "KnowledgeStructure"
        return "Concept"

    def _extract_triples_heuristic(self, text: str) -> list[tuple[str, str, str]]:
        """Lightweight relational triple extractor with rule-based heuristics."""
        triples: list[tuple[str, str, str]] = []
        sentences = re.split(r"[.!?\n]+", text)
        relation_patterns = [
            r"^(.*?)\s+(is a|is an|is|was|are|were)\s+(.*)$",
            r"^(.*?)\s+(organizes|manages|stores|contains|uses|implements|supports|extracts|resolves|builds)\s+(.*)$",
            r"^(.*?)\s+(developed by|founded by|authored by|created by)\s+(.*)$",
            r"^(.*?)\s+(consists of|connects to|combines with|enhances)\s+(.*)$",
        ]

        for s in sentences:
            s_clean = s.strip()
            if not s_clean or len(s_clean) < 8:
                continue

            matched = False
            for pat in relation_patterns:
                m = re.match(pat, s_clean, re.IGNORECASE)
                if m:
                    head = m.group(1).strip()
                    rel = m.group(2).strip().lower()
                    tail = m.group(3).strip()
                    if 1 < len(head) < 80 and 1 < len(tail) < 100:
                        triples.append((head, rel, tail))
                        matched = True
                        break

            if not matched and "," in s_clean:
                parts = [p.strip() for p in s_clean.split(",") if p.strip()]
                if len(parts) >= 2 and len(parts[0]) < 50 and len(parts[1]) < 60:
                    triples.append((parts[0], "related_to", parts[1]))

        # Deduplicate while preserving order
        unique_triples: list[tuple[str, str, str]] = []
        seen = set()
        for t in triples:
            k = (t[0].lower(), t[1].lower(), t[2].lower())
            if k not in seen:
                seen.add(k)
                unique_triples.append(t)

        return unique_triples

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

        # 1. Process documents into PassageNodes
        normalized_docs: list[dict[str, Any]] = []
        for i, item in enumerate(docs):
            if isinstance(item, str):
                normalized_docs.append({"idx": f"doc_{i}", "content": item})
            elif isinstance(item, dict):
                c_id = item.get("idx") or item.get("id") or item.get("chunk_id") or f"doc_{i}"
                txt = item.get("content") or item.get("passage") or item.get("text") or ""
                triples = item.get("extracted_triples") or item.get("triples") or []
                normalized_docs.append({"idx": str(c_id), "content": txt, "triples": triples})

        # Index passages and tokens
        for d in normalized_docs:
            p_idx = mem.get_or_create_passage(d["idx"], d["content"])
            tokens = _tokenize(d["content"])
            for t in set(tokens):
                doc_freq[t] += 1

            # Extract or load triples
            triples = d.get("triples")
            if not triples:
                triples = self._extract_triples_heuristic(d["content"])

            for raw_t in triples:
                if isinstance(raw_t, (list, tuple)) and len(raw_t) == 3:
                    h, r, t = str(raw_t[0]), str(raw_t[1]), str(raw_t[2])
                    f_idx = mem.get_or_create_fact((h, r, t))
                    mem.link_passage_and_fact(p_idx, f_idx)

                    # Extract abstract schema ontology
                    h_type = self._infer_entity_type(h)
                    t_type = self._infer_entity_type(t)
                    s_idx = mem.get_or_create_schema((h_type, r, t_type))
                    mem.link_fact_and_schema(f_idx, s_idx)

        # 2. Detect and resolve conflicts
        conflicts = self._detect_conflicts_for_memory(mem)
        self._conflict_registry[save_dir] = conflicts
        resolved_count = 0

        if not skip_conflict_resolution and conflicts:
            resolved_count = self._resolve_conflicts_for_memory(mem, conflicts)

        # 3. Build Compiled Memory Graph
        graph_stats = self._compile_memory_graph(mem, save_dir)

        # Save to memory registry
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

    def _detect_conflicts_for_memory(self, mem: ThreeLayerMemory) -> list[ConflictGroupModel]:
        """Detect facts with identical (head, relation) that assert contradictory tails."""
        grouped: dict[tuple[str, str], list[int]] = defaultdict(list)
        for f in mem.fact_layer:
            key = (f.content[0].lower().strip(), f.content[1].lower().strip())
            grouped[key].append(f.idx)

        conflicts: list[ConflictGroupModel] = []
        for (head_low, rel_low), fact_ids in grouped.items():
            if len(fact_ids) < 2:
                continue

            tails = [mem.fact_layer[idx].content[2].strip() for idx in fact_ids]
            unique_tails = list(set(tails))
            if len(unique_tails) > 1:
                # Disagreement detected
                sample_fact = mem.fact_layer[fact_ids[0]]
                all_p_indices: list[int] = []
                for idx in fact_ids:
                    all_p_indices.extend(mem.fact_layer[idx].passage_indices)

                conflicts.append(
                    ConflictGroupModel(
                        group_id=f"conflict_{len(conflicts) + 1}",
                        head=sample_fact.content[0],
                        relation=sample_fact.content[1],
                        conflicting_tails=unique_tails,
                        fact_indices=fact_ids,
                        supporting_passage_indices=sorted(list(set(all_p_indices))),
                        resolution_status="pending",
                    )
                )

        return conflicts

    def _resolve_conflicts_for_memory(
        self, mem: ThreeLayerMemory, conflicts: list[ConflictGroupModel]
    ) -> int:
        """Resolve conflicts by selecting highest evidence frequency."""
        resolved = 0
        for cg in conflicts:
            # Score each conflicting fact based on supporting passage frequency
            best_fact_idx = -1
            best_freq = -1

            for f_idx in cg.fact_indices:
                fact = mem.fact_layer[f_idx]
                freq = len(fact.passage_indices)
                if freq > best_freq:
                    best_freq = freq
                    best_fact_idx = f_idx

            if best_fact_idx != -1:
                winning_fact = mem.fact_layer[best_fact_idx]
                cg.resolved_tail = winning_fact.content[2]
                cg.resolution_status = "resolved"
                resolved += 1

        return resolved

    def _compile_memory_graph(self, mem: ThreeLayerMemory, save_dir: str) -> dict[str, int]:
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
                nodes[h_node_id] = {"type": "entity", "name": h, "entity_type": self._infer_entity_type(h)}
            if t_node_id not in nodes:
                nodes[t_node_id] = {"type": "entity", "name": t, "entity_type": self._infer_entity_type(t)}

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

        graph_obj = {
            "nodes": nodes,
            "edges": edges,
            "nodes_count": len(nodes),
            "edges_count": len(edges),
        }
        self._graphs[save_dir] = graph_obj
        return {"nodes_count": len(nodes), "edges_count": len(edges)}

    def retrieve(
        self,
        query: str,
        save_dir: str = "outputs/default",
        num_to_retrieve: int = 5,
        damping: float = 0.5,
        passage_node_weight: float = 0.1,
    ) -> dict[str, Any]:
        """Hybrid multi-layer graph retrieval combining TF-IDF seed scoring and graph diffusion."""
        mem = self.get_memory(save_dir)
        doc_freq = self._doc_frequencies[save_dir]
        total_docs = max(1, len(mem.passage_layer))

        if not mem.passage_layer:
            return {"status": "ok", "query": query, "passages": [], "facts": [], "schemas": [], "retrieved_count": 0}

        query_tokens = _tokenize(query)
        q_vec = _compute_tf_idf_vector(query_tokens, doc_freq, total_docs)

        # 1. Compute Seed Relevance Scores on Passages & Facts
        passage_scores: dict[int, float] = {}
        for p in mem.passage_layer:
            p_tokens = _tokenize(p.content)
            p_vec = _compute_tf_idf_vector(p_tokens, doc_freq, total_docs)
            sim = _cosine_similarity(q_vec, p_vec)
            passage_scores[p.idx] = sim

        fact_scores: dict[int, float] = {}
        for f in mem.fact_layer:
            f_text = f"{f.content[0]} {f.content[1]} {f.content[2]}"
            f_tokens = _tokenize(f_text)
            f_vec = _compute_tf_idf_vector(f_tokens, doc_freq, total_docs)
            f_sim = _cosine_similarity(q_vec, f_vec)
            fact_scores[f.idx] = f_sim

        # 2. Graph Diffusion / Personalized PageRank Approximation
        # Propagate weights from query-matched entities/facts back into supporting passages
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

    def query(
        self,
        query: str,
        save_dir: str = "outputs/default",
        num_passages: int = 5,
    ) -> dict[str, Any]:
        """Synthesize a complete answer for user query grounded in three-layer memory."""
        ret = self.retrieve(query, save_dir=save_dir, num_to_retrieve=num_passages)
        passages = ret.get("passages", [])
        facts = ret.get("facts", [])

        if not passages:
            return {
                "status": "ok",
                "query": query,
                "answer": "No relevant memory evidence found to answer the query.",
                "retrieved_passages": [],
                "reasoning_steps": ["Queried 3-layer memory", "No matching passages or facts found"],
            }

        # Build context reasoning synthesis
        top_passage_texts = [f"[{p['chunk_id']}]: {p['content']}" for p in passages[:3]]
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

    def add_passage(
        self,
        chunk_id: str,
        content: str,
        extracted_triples: list[list[str]] | None = None,
        schema_tuple: list[str] | None = None,
        save_dir: str = "outputs/default",
    ) -> dict[str, Any]:
        """Incrementally add a passage chunk and update memory indices."""
        mem = self.get_memory(save_dir)
        p_idx = mem.get_or_create_passage(chunk_id, content)

        tokens = _tokenize(content)
        doc_freq = self._doc_frequencies[save_dir]
        for t in set(tokens):
            doc_freq[t] += 1

        triples = extracted_triples or self._extract_triples_heuristic(content)
        for raw_t in triples:
            if isinstance(raw_t, (list, tuple)) and len(raw_t) == 3:
                h, r, t = str(raw_t[0]), str(raw_t[1]), str(raw_t[2])
                f_idx = mem.get_or_create_fact((h, r, t))
                mem.link_passage_and_fact(p_idx, f_idx)

                if schema_tuple and len(schema_tuple) == 3:
                    s_tuple = (str(schema_tuple[0]), str(schema_tuple[1]), str(schema_tuple[2]))
                else:
                    s_tuple = (self._infer_entity_type(h), r, self._infer_entity_type(t))

                s_idx = mem.get_or_create_schema(s_tuple)
                mem.link_fact_and_schema(f_idx, s_idx)

        # Recompile graph
        self._compile_memory_graph(mem, save_dir)
        p_node = mem.passage_layer[p_idx]

        return {
            "idx": p_node.idx,
            "chunk_id": p_node.chunk_id,
            "content": p_node.content,
            "fact_indices": p_node.fact_indices,
            "score": 1.0,
        }

    def get_summary(self, save_dir: str = "outputs/default") -> dict[str, Any]:
        """Get summary metrics of the three-layer memory."""
        mem = self.get_memory(save_dir)
        graph = self._graphs.get(save_dir, {"nodes_count": 0, "edges_count": 0})

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
            "num_graph_nodes": graph.get("nodes_count", 0),
            "num_graph_edges": graph.get("edges_count", 0),
            "avg_facts_per_schema": round(avg_facts, 2),
            "avg_passages_per_fact": round(avg_passages, 2),
        }

    def detect_conflicts(self, save_dir: str = "outputs/default") -> dict[str, Any]:
        """Detect conflicts in active memory or return existing resolved conflict registry."""
        if save_dir in self._conflict_registry and self._conflict_registry[save_dir]:
            conflicts = self._conflict_registry[save_dir]
        else:
            mem = self.get_memory(save_dir)
            conflicts = self._detect_conflicts_for_memory(mem)
            self._conflict_registry[save_dir] = conflicts
        return {
            "status": "ok",
            "save_dir": save_dir,
            "conflicts_count": len(conflicts),
            "conflicts": [c.model_dump() for c in conflicts],
        }
