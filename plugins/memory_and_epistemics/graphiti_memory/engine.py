"""Bi-temporal Knowledge Graph Engine with Tri-brid Search & Balanced Merge."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from .models import EntityEdge, EntityNode, EpisodicNode, _utc_now


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric words and subwords."""
    words = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\w+", text)
    tokens: list[str] = []
    for w in words:
        low = w.lower()
        if len(low) > 1:
            tokens.append(low)
    return tokens


def _compute_tf_idf(tokens: list[str], doc_freq: dict[str, int], total_docs: int) -> dict[str, float]:
    """Compute normalized TF-IDF vector for tokens."""
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


class GraphitiMemoryEngine:
    """In-memory bi-temporal knowledge graph engine."""

    def __init__(self) -> None:
        # Partitioned storage: group_id -> dict
        self._episodes: dict[str, dict[str, EpisodicNode]] = defaultdict(dict)
        self._entities: dict[str, dict[str, EntityNode]] = defaultdict(dict)  # uuid -> node
        self._entity_names: dict[str, dict[str, str]] = defaultdict(dict)  # lower_name -> uuid
        self._edges: dict[str, dict[str, EntityEdge]] = defaultdict(dict)  # uuid -> edge

        # Indexing for Tri-brid Search
        self._doc_freq: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._adjacency: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))  # node_uuid -> [edge_uuid]

    def _extract_relations(self, content: str) -> list[dict[str, str]]:
        """Heuristic semantic relation and entity extractor from episodic text."""
        extracted: list[dict[str, str]] = []
        # Split into sentences or lines
        raw_segments = re.split(r"[.\n;]+", content)
        sentences = [s.strip() for s in raw_segments if s.strip()]

        # Common relational patterns
        patterns = [
            r"(?P<src>[A-Z][A-Za-z0-9_\-\s]{1,30}?)\s+(?:is located in|lives in|moved to|relocated to)\s+(?P<tgt>[A-Z][A-Za-z0-9_\-\s]{1,30})",
            r"(?P<src>[A-Z][A-Za-z0-9_\-\s]{1,30}?)\s+(?:uses|adopts|migrated to|switched to)\s+(?P<tgt>[A-Z][A-Za-z0-9_\-\s]{1,30})",
            r"(?P<src>[A-Z][A-Za-z0-9_\-\s]{1,30}?)\s+(?:prefers|favors|selected)\s+(?P<tgt>[A-Z][A-Za-z0-9_\-\s]{1,30})",
            r"(?P<src>[A-Z][A-Za-z0-9_\-\s]{1,30}?)\s+(?:implements|extends|integrates with)\s+(?P<tgt>[A-Z][A-Za-z0-9_\-\s]{1,30})",
            r"(?P<src>[A-Z][A-Za-z0-9_\-\s]{1,30}?)\s+(?:depends on|requires|connects to)\s+(?P<tgt>[A-Z][A-Za-z0-9_\-\s]{1,30})",
            r"(?P<src>[A-Z][A-Za-z0-9_\-\s]{1,30}?)\s+is\s+(?:a|an)\s+(?P<tgt>[A-Za-z0-9_\-\s]{2,30})",
        ]

        rel_mapping = {
            "is located in": "LOCATED_IN",
            "lives in": "LIVES_IN",
            "moved to": "LIVES_IN",
            "relocated to": "LIVES_IN",
            "uses": "USES",
            "adopts": "USES",
            "migrated to": "USES",
            "switched to": "USES",
            "prefers": "PREFERS",
            "favors": "PREFERS",
            "selected": "PREFERS",
            "implements": "IMPLEMENTS",
            "extends": "EXTENDS",
            "integrates with": "INTEGRATES_WITH",
            "depends on": "DEPENDS_ON",
            "requires": "REQUIRES",
            "connects to": "CONNECTS_TO",
            "is a": "IS_A",
            "is an": "IS_A",
        }

        for sentence in sentences:
            matched = False
            for pat in patterns:
                m = re.search(pat, sentence, re.IGNORECASE)
                if m:
                    src = m.group("src").strip()
                    tgt = m.group("tgt").strip()
                    if src and tgt and src.lower() != tgt.lower():
                        # Determine relation type
                        matched_rel = "RELATES_TO"
                        lower_sentence = sentence.lower()
                        for verb, rel_type in rel_mapping.items():
                            if verb in lower_sentence:
                                matched_rel = rel_type
                                break

                        extracted.append({
                            "source": src,
                            "target": tgt,
                            "relation": matched_rel,
                            "fact": sentence,
                        })
                        matched = True
                        break

            # Fallback noun phrase pairing if sentence has multiple capitalized nouns
            if not matched:
                capitals = re.findall(r"\b[A-Z][A-Za-z0-9_\-]{2,}\b", sentence)
                if len(capitals) >= 2:
                    extracted.append({
                        "source": capitals[0],
                        "target": capitals[1],
                        "relation": "MENTIONED_WITH",
                        "fact": sentence,
                    })

        return extracted

    def add_episode(
        self,
        content: str,
        group_id: str = "default",
        source_description: str = "interaction",
    ) -> tuple[EpisodicNode, list[EntityNode], list[EntityEdge], int]:
        """Ingest episodic text, extract entities and facts, and invalidate contradictions."""
        now = _utc_now()
        episode = EpisodicNode(
            group_id=group_id,
            content=content,
            source_description=source_description,
            created_at=now,
        )

        extracted_relations = self._extract_relations(content)
        new_or_updated_entities: dict[str, EntityNode] = {}
        new_or_updated_edges: list[EntityEdge] = []
        invalidated_count = 0

        # Helper to get or create EntityNode
        def _get_or_create_entity(name: str) -> EntityNode:
            clean_name = name.strip()
            lower_name = clean_name.lower()
            existing_uuid = self._entity_names[group_id].get(lower_name)

            if existing_uuid and existing_uuid in self._entities[group_id]:
                node = self._entities[group_id][existing_uuid]
                node.updated_at = now
                if episode.uuid not in node.episodes:
                    node.episodes.append(episode.uuid)
                return node

            # Create new entity
            new_node = EntityNode(
                group_id=group_id,
                name=clean_name,
                summary=f"Entity {clean_name} introduced in episode {episode.uuid[:8]}.",
                created_at=now,
                updated_at=now,
                episodes=[episode.uuid],
            )
            self._entities[group_id][new_node.uuid] = new_node
            self._entity_names[group_id][lower_name] = new_node.uuid
            return new_node

        for rel in extracted_relations:
            src_node = _get_or_create_entity(rel["source"])
            tgt_node = _get_or_create_entity(rel["target"])
            rel_name = rel["relation"]

            new_or_updated_entities[src_node.uuid] = src_node
            new_or_updated_entities[tgt_node.uuid] = tgt_node

            # Bi-Temporal Invalidation Check:
            # Check for existing active relations of the same type for this source node
            # (e.g. LIVES_IN, PREFERS, USES) where target is different
            if rel_name in ("LIVES_IN", "LOCATED_IN", "PREFERS", "USES", "MIGRATED_TO"):
                for existing_edge in self._edges[group_id].values():
                    if (
                        existing_edge.source_node_uuid == src_node.uuid
                        and existing_edge.relation_name == rel_name
                        and existing_edge.invalid_at is None
                        and existing_edge.target_node_uuid != tgt_node.uuid
                    ):
                        existing_edge.invalid_at = now
                        invalidated_count += 1

            # Create new EntityEdge
            edge = EntityEdge(
                group_id=group_id,
                source_node_uuid=src_node.uuid,
                source_name=src_node.name,
                target_node_uuid=tgt_node.uuid,
                target_name=tgt_node.name,
                relation_name=rel_name,
                fact=rel["fact"],
                episodes=[episode.uuid],
                valid_at=now,
                invalid_at=None,
            )
            self._edges[group_id][edge.uuid] = edge
            self._adjacency[group_id][src_node.uuid].append(edge.uuid)
            self._adjacency[group_id][tgt_node.uuid].append(edge.uuid)
            new_or_updated_edges.append(edge)

            # Update document frequency tokens
            tokens = _tokenize(f"{src_node.name} {tgt_node.name} {rel_name} {rel['fact']}")
            for t in set(tokens):
                self._doc_freq[group_id][t] += 1

        episode.extracted_entities = [n.name for n in new_or_updated_entities.values()]
        episode.extracted_edges = [e.uuid for e in new_or_updated_edges]
        self._episodes[group_id][episode.uuid] = episode

        return episode, list(new_or_updated_entities.values()), new_or_updated_edges, invalidated_count

    def search(
        self,
        query: str,
        group_id: str = "default",
        limit: int = 5,
        include_invalidated: bool = False,
    ) -> list[tuple[EntityEdge, float]]:
        """Tri-brid search: Dense vector similarity + Sparse BM25 + BFS graph proximity with Balanced Merge."""
        edges = list(self._edges[group_id].values())
        if not edges:
            return []

        active_edges = edges if include_invalidated else [e for e in edges if e.invalid_at is None]
        if not active_edges:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return [(e, 1.0) for e in active_edges[:limit]]

        total_docs = len(active_edges)
        doc_freq = self._doc_freq[group_id]
        q_vec = _compute_tf_idf(query_tokens, doc_freq, total_docs)

        # 1. Dense Semantic Scoring (Cosine similarity over edge content TF-IDF)
        dense_scores: list[tuple[EntityEdge, float]] = []
        for edge in active_edges:
            edge_tokens = _tokenize(f"{edge.source_name} {edge.target_name} {edge.relation_name} {edge.fact}")
            e_vec = _compute_tf_idf(edge_tokens, doc_freq, total_docs)
            score = sum(q_w * e_vec.get(t, 0.0) for t, q_w in q_vec.items())
            if score > 0:
                dense_scores.append((edge, score))
        dense_scores.sort(key=lambda x: x[1], reverse=True)

        # 2. Sparse Exact Matching (Token intersection overlap)
        sparse_scores: list[tuple[EntityEdge, float]] = []
        q_set = set(query_tokens)
        for edge in active_edges:
            edge_tokens = set(_tokenize(f"{edge.source_name} {edge.target_name} {edge.relation_name} {edge.fact}"))
            overlap = len(q_set.intersection(edge_tokens))
            if overlap > 0:
                score = overlap / max(1, len(q_set))
                sparse_scores.append((edge, score))
        sparse_scores.sort(key=lambda x: x[1], reverse=True)

        # 3. BFS Graph Proximity Scoring (find matching entity anchors and traverse neighbors)
        matched_node_uuids = set()
        for term in q_set:
            if term in self._entity_names[group_id]:
                matched_node_uuids.add(self._entity_names[group_id][term])

        bfs_edges: list[tuple[EntityEdge, float]] = []
        for node_uuid in matched_node_uuids:
            incident_edge_uuids = self._adjacency[group_id].get(node_uuid, [])
            for e_uuid in incident_edge_uuids:
                edge = self._edges[group_id].get(e_uuid)
                if edge and (include_invalidated or edge.invalid_at is None):
                    bfs_edges.append((edge, 0.85))

        # 4. Balanced Merge Interleave & Reciprocal Rank Fusion (RRF)
        # RRF score = sum( 1.0 / (60 + rank_i) )
        rrf_scores: dict[str, float] = defaultdict(float)
        edge_map: dict[str, EntityEdge] = {}

        for rank, (edge, _) in enumerate(dense_scores):
            rrf_scores[edge.uuid] += 1.0 / (60.0 + rank + 1)
            edge_map[edge.uuid] = edge

        for rank, (edge, _) in enumerate(sparse_scores):
            rrf_scores[edge.uuid] += 1.0 / (60.0 + rank + 1)
            edge_map[edge.uuid] = edge

        for rank, (edge, _) in enumerate(bfs_edges):
            rrf_scores[edge.uuid] += 1.0 / (60.0 + rank + 1)
            edge_map[edge.uuid] = edge

        ranked_edges = sorted(
            [(edge_map[e_uuid], round(score * 100, 4)) for e_uuid, score in rrf_scores.items()],
            key=lambda x: x[1],
            reverse=True,
        )

        return ranked_edges[:limit]

    def get_entity(self, name_or_uuid: str, group_id: str = "default") -> EntityNode | None:
        """Look up entity node by canonical name or UUID."""
        # Check direct UUID lookup
        if name_or_uuid in self._entities[group_id]:
            return self._entities[group_id][name_or_uuid]

        # Check name lookup
        lower_name = name_or_uuid.strip().lower()
        if lower_name in self._entity_names[group_id]:
            uuid_val = self._entity_names[group_id][lower_name]
            return self._entities[group_id].get(uuid_val)

        return None

    def get_entity_relations(self, entity_uuid: str, group_id: str = "default", include_invalidated: bool = False) -> list[EntityEdge]:
        """Retrieve all incident relationship edges for a given entity."""
        edge_uuids = self._adjacency[group_id].get(entity_uuid, [])
        results: list[EntityEdge] = []
        for e_uuid in edge_uuids:
            edge = self._edges[group_id].get(e_uuid)
            if edge and (include_invalidated or edge.invalid_at is None):
                results.append(edge)
        return results

    def invalidate_fact(self, edge_uuid: str, reason: str = "Contradicted") -> EntityEdge | None:
        """Mark an existing fact edge as invalidated."""
        now = _utc_now()
        for group_id, edges in self._edges.items():
            if edge_uuid in edges:
                edge = edges[edge_uuid]
                edge.invalid_at = now
                return edge
        return None

    def get_status(self, group_id: str = "default") -> dict[str, Any]:
        """Compute memory graph volume and active facts."""
        episodes = self._episodes[group_id]
        entities = self._entities[group_id]
        edges = self._edges[group_id]

        active_count = sum(1 for e in edges.values() if e.invalid_at is None)
        invalidated_count = sum(1 for e in edges.values() if e.invalid_at is not None)

        return {
            "status": "ok",
            "backend": "in_process_temporal_graph",
            "group_id": group_id,
            "total_episodes": len(episodes),
            "total_entities": len(entities),
            "total_facts": len(edges),
            "active_facts": active_count,
            "invalidated_facts": invalidated_count,
        }
