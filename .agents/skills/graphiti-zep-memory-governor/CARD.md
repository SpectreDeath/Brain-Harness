```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: graphiti-zep-memory-governor                                  │
│ Category: memory_and_epistemics / temporal_knowledge_graph           │
│ Version: 1.0.0                                                       │
│ Invocation: /graphiti-zep-memory-governor                            │
│ Triggers: "getzep", "graphiti", "zep-python", "bitemporal",          │
│           "MinHash", "LSH", "rrf", "mmr", "build_ontology"           │
│ Requires: "epistemic-memory-lifecycle"                               │
│ Target: Temporal KG edges, entity dedup, RRF/MMR & Zep ontologies    │
└──────────────────────────────────────────────────────────────────────┘
```

# Graphiti Zep Memory Governor — Companion Summary Card

## Pipeline Stages

| Stage | Operation | Output Model |
| --- | --- | --- |
| **1. Temporal Bounds** | `normalize_bitemporal_edges()` | `BiTemporalEdgeNormalizationReport` (`normalized_valid_at`, `soft_deadline_cleared`) |
| **2. Entity Dedup** | `resolve_entities_and_endpoints()` | `EntityDedupResolutionReport` (`duplicate_pairs`, `llm_deferred_names`, `pruned_endpoints`) |
| **3. Hybrid Rerank** | `rerank_hybrid_results()` | `HybridRerankReport` (`method`, `ranked_uuids`, `scores`) |
| **4. Community/Schema** | `cluster_communities_and_compile_ontology()` | `CommunityAndOntologyReport` (`communities`, `group_queue_depths`, `ontology_valid`) |

---

## Mandatory Invariants Checklist

- [ ] **Future Assertion Clamping**: Planned facts clamp `valid_at > reference_time` to `reference_time` and clear soft `_DEADLINE_RE` `invalid_at` unless `_ONGOING_STATE_END_RE` matches.
- [ ] **Entropy & LSH Thresholds**: Names below Shannon entropy `1.5` (or length `< 6` and `< 2` tokens) defer to LLM resolution; high-entropy merges require 32-perm 4-band MinHash/LSH with Jaccard `>= 0.9`.
- [ ] **Endpoint Hygiene & Ranking Normalization**: Unreferenced materialized endpoints are pruned, MMR L2-normalizes vectors, and `node_distance` pins `center_node_uuid` at `0.1`.
- [ ] **Group Queue & Ontology Guards**: Every episode carries non-empty `group_id`, entity/edge types carry descriptions, and `Identity` markers never appear on edges.
- [ ] **Slotted & Frozen Models**: All four report dataclasses use `slots=True, frozen=True` (Rule 12).
