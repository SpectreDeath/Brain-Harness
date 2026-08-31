# Cross-Brain Knowledge Distillation via TF-IDF

## Problem
Knowledge trapped in foreign agent brains, IDE transcripts, and knowledge vaults is inaccessible to the host harness without manual review.

## Solution
Use `plugin.brain_bridge` to mount external directories and index them with TF-IDF:
1. `brain_attach` detects format, chunks files, indexes transcripts, and builds normalized vectors.
2. `brain_query` performs cosine similarity search across mounted chunks.
3. The 4-axis introspection matrix queries architectural logic, error trajectories, epistemic habits, and delta learnings.

## Operational Guideline
When distilling knowledge from an external brain:
- Attach in `lens` mode to preserve read-only isolation.
- Run all 4 axes before synthesizing KIs.
- Use `top_k=10` for initial exploration, then narrow to top-3 for final commits.
- Always include exact file paths and line ranges in Isnad provenance.

## Provenance
- Source brain: `antigravity_core`
- Primary source: `c5505b1b-eed6-40d3-b07d-0e060e559d5f.system_generated/logs/transcript_full.jsonl#L37`
- Distilled from: mind-reader skill design, attach summary (53,017 unique terms, 77,716 chunks)