# Graphiti: Entropy-Gated MinHash/LSH Deduplication & Dangling Endpoints

## Overview
- **Source Repository**: `https://github.com/getzep/graphiti` (`ed231965`)
- **Primary Files**:
  - `graphiti_core/utils/maintenance/dedup_helpers.py#L31-L190`
  - `graphiti_core/utils/maintenance/dangling_endpoints.py#L26-L74`

## Core Architecture & Invariants
1. **Entropy Specificity Gate (`_has_high_entropy`)**: Names shorter than `_MIN_NAME_LENGTH = 6` with `< _MIN_TOKEN_COUNT = 2` tokens, or character Shannon entropy `< _NAME_ENTROPY_THRESHOLD = 1.5`, are deferred to LLM resolution instead of risking false fuzzy merges.
2. **MinHash / LSH Candidate Indexing**: High-entropy normalized names produce character 3-gram shingles, `_MINHASH_PERMUTATIONS = 32` 64-bit `blake2b` MinHash signatures, and `_MINHASH_BAND_SIZE = 4` LSH buckets, confirming candidates at Jaccard similarity `>= 0.9`.
3. **Label Promotion (`_promote_resolved_node`)**: Merging an extracted entity into an existing node promotes specific labels while preserving `'Entity'` (`ENTITY_BASE_LABEL`) first without duplicates.
4. **Dangling Endpoint Hygiene**: Edge endpoints absent from the extracted entity list are temporarily materialized via `materialize_dangling_endpoint_node()`, then orphaned endpoints dropped by edge filtering are garbage-collected by `prune_unreferenced_materialized_nodes()`.

## Decision Heuristics & Anti-Patterns
- **Never run n-gram fuzzy dedup on short/repetitive acronyms or codes**: Defer low-entropy strings to semantic disambiguation.
- **Never commit orphan materialized nodes after edge filtering**: Prune unreferenced endpoints against surviving edges.
