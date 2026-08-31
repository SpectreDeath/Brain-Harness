# KI-2: Tri-brid Search Fusion with Balanced Merge for Knowledge Graphs

## Overview & Retrieval Dynamics
Querying complex relational graphs requires balancing three distinct information retrieval modalities:
1. **Dense Vector Search**: Captures semantic synonyms, paraphrases, and intent.
2. **Sparse Fulltext (BM25)**: Captures exact identifier tokens, acronyms, code symbols, and proper nouns.
3. **Graph Neighborhood Traversal (BFS)**: Captures direct multi-hop relational context surrounding query entity anchors.

## The Balanced Merge Solution

In `graphiti_core/search/search.py` and commit `d40da88f`:
```python
# Rather than summing heterogeneous cosine and BM25 scores:
# 1. Retrieve top-N candidates from each channel independently
vector_results = await driver.search_ops.search_nodes_by_vector(query_vector, limit=limit)
text_results = await driver.search_ops.search_nodes_by_fulltext(query_text, limit=limit)
bfs_results = await driver.search_ops.edge_bfs_search(center_node_uuids, max_depth=2, limit=limit)

# 2. Interleave into a balanced candidate shortlist
candidate_nodes = balanced_merge(
    [vector_results, text_results, bfs_results],
    max_total=config.cross_encoder_shortlist_size
)

# 3. Apply Cross-Encoder (e.g. BGE / Gemini / OpenAI) over full query-document pairs
reranked_results = await cross_encoder.rank(query, candidate_nodes)
```

## Architectural Benefits
- Prevents high-confidence vector matches from monopolizing the candidate window when exact keyword matches or immediate graph neighbors are critical.
- Separates fast candidate generation ($O(K)$ retrieval) from high-precision reranking ($O(M)$ transformer cross-attention).
