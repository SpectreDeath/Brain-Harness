# High-Scale Trajectory Ingestion & Overlapping Token Indexing

## Problem
Agent trajectory logs and transcript archives scale into hundreds of thousands of lines. Querying these histories with brute-force regex or embedding models is slow, token-prohibitive, and requires heavy dependencies.

## Solution
`plugin.brain_bridge` uses a lightweight, in-memory TF-IDF index:
- **Sliding Chunking**: 30-line slices with 5-line overlaps (step 25).
- **Subword Tokenization**: Regex splitting on camelCase, snake_case, and punctuation boundaries.
- **Normalized Vector Search**: Precomputed cosine similarity for instant top-k retrieval across 84,000+ chunks.

## Operational Guideline
- Keep chunk sizes within 30-50 lines to maintain localized semantic context.
- Use `attach_mode: "lens"` for read-only ephemeral analysis to avoid mounting large histories in persistent state.

## Provenance
- Source Target: [`plugins/memory_and_epistemics/brain_bridge/main.py:L45-75`](file:///d:/GitHub/projects/Brain%20Harness/plugins/memory_and_epistemics/brain_bridge/main.py#L45-L75)
- Verification Run: [`mind-reader-results.json:L9-27`](file:///d:/GitHub/projects/Brain%20Harness/.harness/mind-reader-results.json#L9-L27)
- Isnad Decision ID: `dec_20260823_02`
