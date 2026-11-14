"""Graphiti / Zep Temporal Memory Governor Service.

Distilled from getzep/graphiti @ ed231965 and getzep/zep-python @ 305d8b3a:
- Bi-temporal EntityEdge timeline normalization (valid_at clamping & soft-deadline filtering) and contradiction invalidation
- Character Shannon entropy gate, 32-perm 64-bit blake2b MinHash + 4-band LSH entity dedup, label promotion & dangling pruning
- Hybrid retrieval reranking via Reciprocal Rank Fusion (RRF), Maximal Marginal Relevance (MMR) & shortest-hop distance
- Edge-weighted label propagation community clustering, per-group queue verification & typed EntityModel/EdgeModel compilation
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import blake2b
import math
import re
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey

NAME_ENTROPY_THRESHOLD: float = 1.5
MIN_NAME_LENGTH: int = 6
MIN_TOKEN_COUNT: int = 2
FUZZY_JACCARD_THRESHOLD: float = 0.9
MINHASH_PERMUTATIONS: int = 32
MINHASH_BAND_SIZE: int = 4
ENTITY_BASE_LABEL: str = "Entity"

DEFAULT_RRF_RANK_CONST: int = 1
DEFAULT_MMR_LAMBDA: float = 0.5
DEFAULT_MMR_MIN_SCORE: float = -2.0
CENTER_NODE_SELF_DISTANCE: float = 0.1

ZEP_WIRE_PROPERTY_TYPES: tuple[str, ...] = ("text", "int", "float", "boolean")
SUPPORTED_RERANK_METHODS: tuple[str, ...] = ("rrf", "mmr", "node_distance")

_FUTURE_ASSERTION_RE = re.compile(
    r"\b("
    r"will|shall|is going to|are going to|going to|"
    r"plans? to|planned to|planning to|"
    r"intends? to|intended to|"
    r"expects? to|expected to|"
    r"promises? to|promised to|"
    r"scheduled to|is scheduled to|are scheduled to|"
    r"set to|aims? to|aimed to|committed to"
    r")\b|[a-z]+'ll\b",
    re.IGNORECASE,
)
_DEADLINE_RE = re.compile(r"\b(by|before|no later than|deadline|due by|due on)\b", re.IGNORECASE)
_ONGOING_STATE_END_RE = re.compile(
    r"\b(until|through|thru|expires?|expired|ends?|ended|ending|stops?|stopped|ceases?|ceased|no longer)\b",
    re.IGNORECASE,
)


@dataclass(slots=True, frozen=True)
class BiTemporalEdgeNormalizationReport:
    """Immutable report for bi-temporal edge normalization and contradiction invalidation."""

    fact: str
    reference_time: str
    normalized_valid_at: str | None
    normalized_invalid_at: str | None
    future_assertion_detected: bool
    soft_deadline_cleared: bool
    contradicted_edge_ids: tuple[str, ...]
    surviving_edge_ids: tuple[str, ...]
    violations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.fact or not self.fact.strip():
            raise ValueError("BiTemporalEdgeNormalizationReport.fact must be non-empty")
        if not self.reference_time or not self.reference_time.strip():
            raise ValueError("BiTemporalEdgeNormalizationReport.reference_time must be non-empty")


@dataclass(slots=True, frozen=True)
class EntityDedupResolutionReport:
    """Immutable report for entropy-gated MinHash/LSH entity dedup and endpoint pruning."""

    resolved_entities: tuple[dict[str, Any], ...]
    duplicate_pairs: tuple[tuple[str, str], ...]
    llm_deferred_names: tuple[str, ...]
    materialized_endpoints: tuple[str, ...]
    pruned_endpoints: tuple[str, ...]
    entropy_scores: dict[str, float]
    violations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.entropy_scores, dict):
            raise TypeError("EntityDedupResolutionReport.entropy_scores must be a dict")


@dataclass(slots=True, frozen=True)
class HybridRerankReport:
    """Immutable report for RRF, MMR, or node-distance hybrid search reranking."""

    method: str
    ranked_uuids: tuple[str, ...]
    scores: tuple[float, ...]
    filtered_count: int
    parameters: dict[str, float | int | str]
    violations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.method not in SUPPORTED_RERANK_METHODS:
            raise ValueError(f"Unsupported rerank method: {self.method!r}")
        if self.filtered_count < 0:
            raise ValueError("HybridRerankReport.filtered_count must be non-negative")


@dataclass(slots=True, frozen=True)
class CommunityAndOntologyReport:
    """Immutable report for label-propagation communities, group queues, and ontology compilation."""

    communities: tuple[tuple[str, ...], ...]
    group_queue_depths: dict[str, int]
    sequential_groups_verified: bool
    compiled_entity_types: tuple[dict[str, Any], ...]
    compiled_edge_types: tuple[dict[str, Any], ...]
    ontology_valid: bool
    violations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.sequential_groups_verified, bool):
            raise TypeError("sequential_groups_verified must be a bool")
        if not isinstance(self.ontology_valid, bool):
            raise TypeError("ontology_valid must be a bool")


@runtime_checkable
class GraphitiZepMemoryProtocol(Protocol):
    """Typed IoC service contract for Graphiti/Zep bi-temporal memory governance."""

    def normalize_bitemporal_edges(
        self,
        fact: str,
        reference_time: str,
        valid_at: str | None = None,
        invalid_at: str | None = None,
        existing_edges: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        contradicted_ids: list[str] | tuple[str, ...] = (),
    ) -> BiTemporalEdgeNormalizationReport: ...

    def resolve_entities_and_endpoints(
        self,
        extracted_entities: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        existing_entities: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        edge_endpoints: list[tuple[str, str]] | tuple[tuple[str, str], ...] = (),
        kept_edge_endpoints: list[tuple[str, str]] | tuple[tuple[str, str], ...] | None = None,
    ) -> EntityDedupResolutionReport: ...

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
    ) -> HybridRerankReport: ...

    def cluster_communities_and_compile_ontology(
        self,
        neighbor_projection: dict[str, list[dict[str, Any]]],
        episode_batches: list[dict[str, str]] | tuple[dict[str, str], ...] = (),
        entity_schemas: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        edge_schemas: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    ) -> CommunityAndOntologyReport: ...


GRAPHITI_ZEP_MEMORY_KEY: ServiceKey[GraphitiZepMemoryProtocol] = ServiceKey("service.graphiti_zep_memory")


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _parse_iso_utc(value: str | None, field_name: str, violations: list[str]) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        violations.append(f"invalid_iso_timestamp:{field_name}:{value}")
        return None
    return _ensure_utc(parsed)


def _normalize_string_exact(name: str) -> str:
    return re.sub(r"[\s]+", " ", name.lower()).strip()


def _normalize_name_for_fuzzy(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9' ]", " ", _normalize_string_exact(name)).strip()
    return re.sub(r"[\s]+", " ", cleaned)


def _name_entropy(normalized_name: str) -> float:
    compact = normalized_name.replace(" ", "")
    if not compact:
        return 0.0
    counts: dict[str, int] = {}
    for ch in compact:
        counts[ch] = counts.get(ch, 0) + 1
    total = len(compact)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def _has_high_entropy(normalized_name: str) -> bool:
    tokens = normalized_name.split()
    if len(normalized_name) < MIN_NAME_LENGTH and len(tokens) < MIN_TOKEN_COUNT:
        return False
    return _name_entropy(normalized_name) >= NAME_ENTROPY_THRESHOLD


def _shingles(normalized_name: str) -> set[str]:
    cleaned = normalized_name.replace(" ", "")
    if len(cleaned) < 3:
        return {cleaned} if cleaned else set()
    return {cleaned[i : i + 3] for i in range(len(cleaned) - 2)}


def _hash_shingle(shingle: str, seed: int) -> int:
    return int.from_bytes(blake2b(f"{seed}:{shingle}".encode(), digest_size=8).digest(), "big")


def _minhash_signature(shingles: set[str]) -> tuple[int, ...]:
    if not shingles:
        return ()
    return tuple(min(_hash_shingle(shingle, seed) for shingle in shingles) for seed in range(MINHASH_PERMUTATIONS))


def _lsh_bands(signature: tuple[int, ...]) -> list[tuple[int, tuple[int, ...]]]:
    bands: list[tuple[int, tuple[int, ...]]] = []
    for idx, start in enumerate(range(0, len(signature), MINHASH_BAND_SIZE)):
        band = signature[start : start + MINHASH_BAND_SIZE]
        if len(band) == MINHASH_BAND_SIZE:
            bands.append((idx, band))
    return bands


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a.intersection(b)) / len(a.union(b))


def _promote_labels(existing_labels: list[str], extracted_labels: list[str]) -> list[str]:
    merged: list[str] = [ENTITY_BASE_LABEL]
    for label in [*existing_labels, *extracted_labels]:
        if label != ENTITY_BASE_LABEL and label not in merged:
            merged.append(label)
    return merged


def _l2_normalize(vec: list[float] | tuple[float, ...]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return [0.0 for _ in vec]
    return [v / norm for v in vec]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=False))


class GraphitiZepMemoryEngine:
    """Pure-Python micro-kernel engine enforcing Graphiti & Zep memory invariants."""

    def normalize_bitemporal_edges(
        self,
        fact: str,
        reference_time: str,
        valid_at: str | None = None,
        invalid_at: str | None = None,
        existing_edges: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        contradicted_ids: list[str] | tuple[str, ...] = (),
    ) -> BiTemporalEdgeNormalizationReport:
        """Normalize future-assertion edge timestamps and partition contradicted edge IDs."""
        violations: list[str] = []
        ref_dt = _parse_iso_utc(reference_time, "reference_time", violations)
        valid_dt = _parse_iso_utc(valid_at, "valid_at", violations)
        invalid_dt = _parse_iso_utc(invalid_at, "invalid_at", violations)

        future_detected = bool(_FUTURE_ASSERTION_RE.search(fact))
        soft_deadline_cleared = False

        if ref_dt is not None and future_detected:
            if valid_dt is None or valid_dt > ref_dt:
                valid_dt = ref_dt
            if (
                invalid_dt is not None
                and invalid_dt > ref_dt
                and _DEADLINE_RE.search(fact)
                and not _ONGOING_STATE_END_RE.search(fact)
            ):
                invalid_dt = None
                soft_deadline_cleared = True

        contradicted_set = {str(cid) for cid in contradicted_ids}
        contradicted_out: list[str] = []
        surviving_out: list[str] = []
        seen_edge_ids: set[str] = set()

        for edge in existing_edges:
            eid = str(edge.get("uuid") or edge.get("id") or "")
            if not eid:
                continue
            seen_edge_ids.add(eid)
            if eid in contradicted_set:
                contradicted_out.append(eid)
            else:
                surviving_out.append(eid)

        for cid in contradicted_ids:
            cid_str = str(cid)
            if cid_str not in seen_edge_ids and cid_str not in contradicted_out:
                contradicted_out.append(cid_str)

        return BiTemporalEdgeNormalizationReport(
            fact=fact,
            reference_time=reference_time,
            normalized_valid_at=valid_dt.isoformat() if valid_dt else None,
            normalized_invalid_at=invalid_dt.isoformat() if invalid_dt else None,
            future_assertion_detected=future_detected,
            soft_deadline_cleared=soft_deadline_cleared,
            contradicted_edge_ids=tuple(contradicted_out),
            surviving_edge_ids=tuple(surviving_out),
            violations=tuple(violations),
        )

    def resolve_entities_and_endpoints(
        self,
        extracted_entities: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        existing_entities: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        edge_endpoints: list[tuple[str, str]] | tuple[tuple[str, str], ...] = (),
        kept_edge_endpoints: list[tuple[str, str]] | tuple[tuple[str, str], ...] | None = None,
    ) -> EntityDedupResolutionReport:
        """Resolve extracted entities via entropy-gated MinHash/LSH and prune unreferenced materialized endpoints."""
        existing_exact: dict[str, dict[str, Any]] = {}
        existing_shingles: dict[str, set[str]] = {}
        existing_by_id: dict[str, dict[str, Any]] = {}
        lsh_index: defaultdict[tuple[int, tuple[int, ...]], list[str]] = defaultdict(list)

        for idx, ent in enumerate(existing_entities):
            name = str(ent.get("name") or "")
            eid = str(ent.get("uuid") or ent.get("id") or f"existing-{idx}")
            labels = list(ent.get("labels") or [ENTITY_BASE_LABEL])
            node_copy = {**ent, "uuid": eid, "name": name, "labels": _promote_labels(labels, [])}
            existing_by_id[eid] = node_copy
            exact_key = _normalize_string_exact(name)
            if exact_key and exact_key not in existing_exact:
                existing_exact[exact_key] = node_copy
            fuzzy_name = _normalize_name_for_fuzzy(name)
            if _has_high_entropy(fuzzy_name):
                sh = _shingles(fuzzy_name)
                existing_shingles[eid] = sh
                sig = _minhash_signature(sh)
                for band in _lsh_bands(sig):
                    lsh_index[band].append(eid)

        resolved_entities: list[dict[str, Any]] = []
        duplicate_pairs: list[tuple[str, str]] = []
        llm_deferred: list[str] = []
        entropy_scores: dict[str, float] = {}
        known_exact_names: set[str] = set(existing_exact.keys())

        for idx, ent in enumerate(extracted_entities):
            name = str(ent.get("name") or "")
            exact_key = _normalize_string_exact(name)
            fuzzy_name = _normalize_name_for_fuzzy(name)
            entropy_scores[name] = round(_name_entropy(fuzzy_name), 4)
            extracted_labels = list(ent.get("labels") or [ENTITY_BASE_LABEL])

            if exact_key in existing_exact:
                target = existing_exact[exact_key]
                target["labels"] = _promote_labels(target["labels"], extracted_labels)
                duplicate_pairs.append((name, str(target["name"])))
                resolved_entities.append({**target, "resolution": "exact_match"})
                known_exact_names.add(exact_key)
                continue

            if not _has_high_entropy(fuzzy_name):
                llm_deferred.append(name)
                resolved_entities.append(
                    {
                        "uuid": str(ent.get("uuid") or f"extracted-{idx}"),
                        "name": name,
                        "labels": _promote_labels([], extracted_labels),
                        "resolution": "deferred_low_entropy",
                    }
                )
                if exact_key:
                    known_exact_names.add(exact_key)
                continue

            sh = _shingles(fuzzy_name)
            sig = _minhash_signature(sh)
            candidate_ids: list[str] = []
            seen_cand: set[str] = set()
            for band in _lsh_bands(sig):
                for cand_id in lsh_index.get(band, ()):
                    if cand_id not in seen_cand:
                        seen_cand.add(cand_id)
                        candidate_ids.append(cand_id)

            matched_target: dict[str, Any] | None = None
            for cand_id in candidate_ids:
                cand_shingles = existing_shingles.get(cand_id, set())
                if _jaccard_similarity(sh, cand_shingles) >= FUZZY_JACCARD_THRESHOLD:
                    matched_target = existing_by_id[cand_id]
                    break

            if matched_target is not None:
                matched_target["labels"] = _promote_labels(matched_target["labels"], extracted_labels)
                duplicate_pairs.append((name, str(matched_target["name"])))
                resolved_entities.append({**matched_target, "resolution": "minhash_lsh_match"})
            else:
                new_node = {
                    "uuid": str(ent.get("uuid") or f"extracted-{idx}"),
                    "name": name,
                    "labels": _promote_labels([], extracted_labels),
                    "resolution": "new_entity",
                }
                resolved_entities.append(new_node)
                if exact_key:
                    known_exact_names.add(exact_key)

        materialized: list[str] = []
        materialized_norm: dict[str, str] = {}
        for src, dst in edge_endpoints:
            for endpoint in (src, dst):
                ep_str = str(endpoint).strip()
                ep_norm = _normalize_string_exact(ep_str)
                if ep_norm and ep_norm not in known_exact_names:
                    known_exact_names.add(ep_norm)
                    materialized.append(ep_str)
                    materialized_norm[ep_norm] = ep_str

        pruned: list[str] = []
        if kept_edge_endpoints is not None:
            referenced_norms: set[str] = set()
            for src, dst in kept_edge_endpoints:
                referenced_norms.add(_normalize_string_exact(str(src)))
                referenced_norms.add(_normalize_string_exact(str(dst)))
            pruned = [raw for norm_name, raw in materialized_norm.items() if norm_name not in referenced_norms]

        return EntityDedupResolutionReport(
            resolved_entities=tuple(resolved_entities),
            duplicate_pairs=tuple(duplicate_pairs),
            llm_deferred_names=tuple(llm_deferred),
            materialized_endpoints=tuple(materialized),
            pruned_endpoints=tuple(pruned),
            entropy_scores=entropy_scores,
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
        """Fuse or rerank retrieval results via RRF, L2-normalized MMR, or shortest-hop distance."""
        if method not in SUPPORTED_RERANK_METHODS:
            raise ValueError(f"Unsupported rerank method {method!r}; expected {SUPPORTED_RERANK_METHODS}")

        violations: list[str] = []
        if method == "rrf":
            effective_k = max(1, int(rank_const))
            rrf_scores: dict[str, float] = defaultdict(float)
            for result in ranked_lists:
                for rank_idx, uuid in enumerate(result):
                    rrf_scores[str(uuid)] += 1.0 / (rank_idx + effective_k)
            sorted_terms = sorted(rrf_scores.items(), key=lambda term: term[1], reverse=True)
            kept = [(u, round(s, 6)) for u, s in sorted_terms if s >= min_score]
            return HybridRerankReport(
                method="rrf",
                ranked_uuids=tuple(u for u, _ in kept),
                scores=tuple(s for _, s in kept),
                filtered_count=len(sorted_terms) - len(kept),
                parameters={"rank_const": effective_k, "min_score": float(min_score)},
                violations=tuple(violations),
            )

        if method == "mmr":
            vectors = candidate_vectors or {}
            if not vectors:
                return HybridRerankReport(
                    method="mmr",
                    ranked_uuids=(),
                    scores=(),
                    filtered_count=0,
                    parameters={"mmr_lambda": float(mmr_lambda), "min_score": float(min_score)},
                    violations=("empty_candidate_vectors",),
                )
            uuids = list(vectors.keys())
            q_norm = _l2_normalize(list(query_vector))
            cand_norm = {u: _l2_normalize(vectors[u]) for u in uuids}

            # Mirror search_utils.py symmetric similarity matrix with zero diagonal
            sim_matrix: list[list[float]] = [[0.0] * len(uuids) for _ in uuids]
            for i, u1 in enumerate(uuids):
                for j, u2 in enumerate(uuids[:i]):
                    sim = _dot(cand_norm[u1], cand_norm[u2])
                    sim_matrix[i][j] = sim
                    sim_matrix[j][i] = sim

            mmr_scores: dict[str, float] = {}
            for i, u in enumerate(uuids):
                max_sim = max(sim_matrix[i]) if len(uuids) > 1 else 0.0
                mmr_val = mmr_lambda * _dot(q_norm, cand_norm[u]) + (mmr_lambda - 1.0) * max_sim
                mmr_scores[u] = round(mmr_val, 6)

            ordered = sorted(uuids, key=lambda u: mmr_scores[u], reverse=True)
            kept_uuids = [u for u in ordered if mmr_scores[u] >= min_score]
            return HybridRerankReport(
                method="mmr",
                ranked_uuids=tuple(kept_uuids),
                scores=tuple(mmr_scores[u] for u in kept_uuids),
                filtered_count=len(ordered) - len(kept_uuids),
                parameters={"mmr_lambda": float(mmr_lambda), "min_score": float(min_score)},
                violations=tuple(violations),
            )

        # node_distance
        distances_in = hop_distances or {}
        if not center_node_uuid:
            violations.append("missing_center_node_uuid")
        all_uuids = list(distances_in.keys())
        if center_node_uuid and center_node_uuid not in all_uuids:
            all_uuids.insert(0, center_node_uuid)

        node_distances: dict[str, float] = {}
        for u in all_uuids:
            if center_node_uuid and u == center_node_uuid:
                node_distances[u] = CENTER_NODE_SELF_DISTANCE
            else:
                dist = float(distances_in.get(u, math.inf))
                node_distances[u] = dist if dist > 0.0 else CENTER_NODE_SELF_DISTANCE

        sorted_nodes = sorted(all_uuids, key=lambda u: node_distances[u])
        node_scores = {u: round(1.0 / node_distances[u], 6) for u in sorted_nodes}
        kept_nodes = [u for u in sorted_nodes if node_scores[u] >= min_score]
        return HybridRerankReport(
            method="node_distance",
            ranked_uuids=tuple(kept_nodes),
            scores=tuple(node_scores[u] for u in kept_nodes),
            filtered_count=len(sorted_nodes) - len(kept_nodes),
            parameters={
                "center_node_uuid": center_node_uuid or "",
                "self_distance": CENTER_NODE_SELF_DISTANCE,
                "min_score": float(min_score),
            },
            violations=tuple(violations),
        )

    def cluster_communities_and_compile_ontology(
        self,
        neighbor_projection: dict[str, list[dict[str, Any]]],
        episode_batches: list[dict[str, str]] | tuple[dict[str, str], ...] = (),
        entity_schemas: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        edge_schemas: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    ) -> CommunityAndOntologyReport:
        """Cluster communities by weighted label propagation, check group queues, and compile typed ontologies."""
        community_map = {uuid: idx for idx, uuid in enumerate(neighbor_projection.keys())}
        max_iters = max(32, len(neighbor_projection) * 4 + 4)

        for _ in range(max_iters):
            no_change = True
            next_map: dict[str, int] = {}
            for uuid, neighbors in neighbor_projection.items():
                curr_comm = community_map[uuid]
                candidates: dict[int, int] = defaultdict(int)
                for nbr in neighbors:
                    nbr_uuid = str(nbr.get("node_uuid") or "")
                    if nbr_uuid in community_map:
                        candidates[community_map[nbr_uuid]] += int(nbr.get("edge_count", 1))
                ranked = sorted(((cnt, comm) for comm, cnt in candidates.items()), reverse=True)
                cand_rank, cand_comm = ranked[0] if ranked else (0, -1)
                if cand_comm != -1 and cand_rank > 1:
                    new_comm = cand_comm
                else:
                    new_comm = max(cand_comm, curr_comm)
                next_map[uuid] = new_comm
                if new_comm != curr_comm:
                    no_change = False
            community_map = next_map
            if no_change:
                break

        clusters_by_id: dict[int, list[str]] = defaultdict(list)
        for uuid, comm in community_map.items():
            clusters_by_id[comm].append(uuid)
        communities = tuple(tuple(sorted(nodes)) for nodes in clusters_by_id.values())

        queue_depths: dict[str, int] = {}
        sequential_ok = True
        violations: list[str] = []
        for idx, ep in enumerate(episode_batches):
            gid = str(ep.get("group_id") or "").strip()
            if not gid:
                sequential_ok = False
                violations.append(f"episode_missing_group_id:{idx}")
                continue
            queue_depths[gid] = queue_depths.get(gid, 0) + 1

        compiled_entities: list[dict[str, Any]] = []
        for schema in entity_schemas:
            label = str(schema.get("name") or "").strip()
            desc = str(schema.get("description") or "").strip()
            if not label:
                violations.append("entity_missing_name")
                continue
            if not desc:
                violations.append(f"entity_missing_description:{label}")
                continue
            props: list[dict[str, str]] = []
            identities: list[str] = []
            for fld in schema.get("fields") or ():
                if fld.get("excluded"):
                    continue
                fname = str(fld.get("name") or "").strip()
                ftype = str(fld.get("type") or "").strip()
                fdesc = str(fld.get("description") or "").strip()
                if ftype not in ZEP_WIRE_PROPERTY_TYPES:
                    violations.append(f"invalid_property_type:{label}.{fname}:{ftype}")
                    continue
                if not fdesc:
                    violations.append(f"field_missing_description:{label}.{fname}")
                    continue
                props.append({"name": fname, "type": ftype, "description": fdesc})
                if fld.get("identity"):
                    identities.append(fname)
            compiled_entities.append(
                {
                    "name": label,
                    "description": desc,
                    "properties": props,
                    "identity_properties": identities or None,
                }
            )

        compiled_edges: list[dict[str, Any]] = []
        for schema in edge_schemas:
            label = str(schema.get("name") or "").strip()
            desc = str(schema.get("description") or "").strip()
            if not label:
                violations.append("edge_missing_name")
                continue
            if not desc:
                violations.append(f"edge_missing_description:{label}")
                continue
            props = []
            for fld in schema.get("fields") or ():
                if fld.get("excluded"):
                    continue
                fname = str(fld.get("name") or "").strip()
                if fld.get("identity"):
                    violations.append(f"edge_identity_forbidden:{label}.{fname}")
                    continue
                ftype = str(fld.get("type") or "").strip()
                fdesc = str(fld.get("description") or "").strip()
                if ftype not in ZEP_WIRE_PROPERTY_TYPES:
                    violations.append(f"invalid_property_type:{label}.{fname}:{ftype}")
                    continue
                if not fdesc:
                    violations.append(f"field_missing_description:{label}.{fname}")
                    continue
                props.append({"name": fname, "type": ftype, "description": fdesc})
            compiled_edges.append(
                {
                    "name": label,
                    "description": desc,
                    "properties": props,
                    "source_targets": list(schema.get("source_targets") or ()),
                }
            )

        return CommunityAndOntologyReport(
            communities=communities,
            group_queue_depths=queue_depths,
            sequential_groups_verified=sequential_ok,
            compiled_entity_types=tuple(compiled_entities),
            compiled_edge_types=tuple(compiled_edges),
            ontology_valid=len([v for v in violations if not v.startswith("episode_")]) == 0,
            violations=tuple(violations),
        )
