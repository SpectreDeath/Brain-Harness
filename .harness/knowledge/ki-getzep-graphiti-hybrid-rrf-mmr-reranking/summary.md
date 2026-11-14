# Graphiti: Hybrid RRF Fusion, MMR & Node-Distance Reranking

## Overview
- **Source Repository**: `https://github.com/getzep/graphiti` (`ed231965`)
- **Primary Files**:
  - `graphiti_core/search/search_utils.py#L1785-L1951`
  - `graphiti_core/search/search_config.py#L1-L120`

## Core Architecture & Invariants
1. **Reciprocal Rank Fusion (`rrf`)**: Accumulates $\sum_r 1 / (\text{rank}_{r}(u) + k)$ across heterogeneous result lists (default `rank_const = 1`), sorts descending, and filters below `min_score`.
2. **Maximal Marginal Relevance (`mmr`)**: L2-normalizes candidate vectors and query vector, computes pairwise cosine similarity matrix, and scores each item $c_i$ as $\lambda (q \cdot c_i) + (\lambda - 1) \max_j (c_i \cdot c_j)$ (`mmr_lambda = 0.5`, `min_score = -2.0`).
3. **Shortest-Hop Centrality (`node_distance_reranker`)**: Assigns `0.1` distance to `center_node_uuid` (`score = 10.0`), `1.0` to direct `RELATES_TO` neighbors, and `inf` (`score = 0.0`) to unlinked nodes before inverse-distance sorting.

## Decision Heuristics & Anti-Patterns
- **Never apply MMR on unnormalized embeddings**: Normalize query and candidate vectors before computing dot-product redundancy penalties.
- **Never collapse disconnected graph nodes above center-node proximity**: Map unreachable distances to `inf` so `1 / inf == 0.0` falls below positive thresholds.
