---
name: graphiti-zep-memory-governor
description: Govern bi-temporal knowledge graphs with Graphiti future-edge clamping, MinHash/LSH entity dedup, RRF/MMR reranking, and Zep typed ontologies. Do not use for static SQL joins or generic web crawling.
---

# Graphiti Zep Memory Governor

`graphiti-zep-memory-governor` distills Graphiti bi-temporal edge normalization and contradiction invalidation, entropy-gated 32-perm MinHash/LSH entity deduplication and dangling endpoint cleanup, RRF/MMR/shortest-hop hybrid search reranking, weighted label-propagation clustering with per-group sequential queues, and Zep typed ontology compilation from `getzep/graphiti` (`ed231965`) and `getzep/zep-python` (`305d8b3a`).

See [CARD.md](CARD.md) for the companion summary card, pipeline stages, and mandatory invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline entropy, LSH, RRF/MMR, and wire property defaults.

---

## 1. Bi-Temporal Edge Normalization & Contradiction Resolution

Separate system ingestion timelines from real-world event truth intervals without corrupting future commitments:

1. **Clamp Future Assertions & Filter Soft Deadlines (`normalize_bitemporal_edges`)**: Detect planned/scheduled assertions (`_FUTURE_ASSERTION_RE`), clamp `valid_at > reference_time` back to `reference_time`, and clear false `invalid_at > reference_time` caused by target deadlines (`_DEADLINE_RE` absent `_ONGOING_STATE_END_RE`).
2. **Preserve Contradiction Audit Trails**: Record contradicted edge UUIDs alongside surviving facts so historical states remain queryable at earlier points in time.

> **Completion criterion**: `BiTemporalEdgeNormalizationReport` normalizes event validity timestamps and partitions contradicted vs surviving edges cleanly.

---

## 2. Entropy-Gated MinHash/LSH Dedup & Dangling Endpoint Hygiene

Eliminate false fuzzy merges on short acronyms while pruning unreferenced synthetic endpoints:

1. **Gate MinHash/LSH Behind Character Shannon Entropy (`resolve_entities_and_endpoints`)**: Defer names below `NAME_ENTROPY_THRESHOLD = 1.5` or shorter than `6` chars with `< 2` tokens to LLM disambiguation; match high-entropy 3-gram shingles via `32`-perm 64-bit `blake2b` MinHash, `4`-band LSH, and `>= 0.9` Jaccard similarity with label promotion (`Entity` first).
2. **Materialize & Prune Dangling Endpoints**: Synthesize missing edge endpoints transiently and garbage-collect any materialized endpoints absent from `kept_edge_endpoints`.

> **Completion criterion**: `EntityDedupResolutionReport` separates deterministic MinHash/LSH merges from low-entropy LLM deferrals and reports surviving vs pruned endpoints.

---

## 3. Hybrid Reranking, Community Clustering & Typed Ontologies

Fuse multi-signal retrieval, detect weighted communities, and validate typed memory schemas:

1. **Rerank Sparse, Dense & Graph Candidates (`rerank_hybrid_results`)**: Fuse multi-source lists via `rrf` (`rank_const = 1`), diversify normalized vectors with `mmr` (`lambda = 0.5`), or rank local neighborhoods with `node_distance` (`center_node` distance `0.1`, unreachable `inf`).
2. **Cluster Communities & Compile Typed Ontologies (`cluster_communities_and_compile_ontology`)**: Run edge-weighted label propagation (`candidate_rank > 1`), verify non-empty `group_id` sequential queue assignment, and compile `EntityModel`/`EdgeModel` schemas across `text`/`int`/`float`/`boolean` while forbidding `Identity` fields on edges.

> **Completion criterion**: `HybridRerankReport` and `CommunityAndOntologyReport` produce deterministic rankings, communities, and schema validation diagnostics.

---

## The Three Foundational Pillars

### 1. Bi-Temporal Timeline Separation with Future-Commitment Clamping
Maintain independent ingestion and world-validity intervals while preventing soft delivery deadlines from falsely invalidating planned assertions.

### 2. Specificity-Gated LSH Deduplication & Endpoint Garbage Collection
Gate probabilistic MinHash/LSH entity merging on character Shannon entropy and prune transiently materialized edge endpoints that lose surviving graph edges.

### 3. Multi-Signal Retrieval Fusion & Typed Group-Serialized Memory
Combine RRF, normalized MMR, and hop-distance reranking atop per-group serialized graph writes and strictly described entity/edge ontologies.

---

## Anti-Patterns

- **Soft Deadlines Written as `invalid_at`** — Saving target dates like "due by Friday" as `invalid_at` without ongoing state-end markers falsely expires active commitments.
- **Unconditional Fuzzy Merging on Low-Entropy Names** — Running 3-gram Jaccard or MinHash matching on short or repetitive identifiers merges unrelated concepts instead of deferring to LLM resolution.
- **Leaking Materialized Dangling Endpoints** — Persisting synthetic placeholder nodes created for edges that are later dropped during filtering pollutes the entity graph.
- **Attaching `Identity` Properties to Edges or Empty Docstrings** — Assigning entity deduplication `Identity` markers to `EdgeModel` fields or omitting type/field descriptions degrades extraction and breaks Zep ontology compilation.
