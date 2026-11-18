# Phase 6 — KI Retrieval Evaluation Summary

## Macro-Average Metrics Across 5 Target Modules

| Method | Precision | Recall | F1 |
|---|---:|---:|---:|
| `hop0` | 0.4000 | 0.2500 | 0.2800 |
| `hop1` | 0.4000 | 0.3000 | 0.3333 |
| `grep_baseline` | 0.8476 | 0.9500 | 0.8769 |

## Per-Module Breakdown

| Module | Gold | Hop-0 (P/R/F1) | Hop-1 (P/R/F1) | Grep Baseline (P/R/F1) |
|---|---:|---|---|---|
| `harness.services.vector_index` | 1 | 1.00/1.00/1.00 | 1.00/1.00/1.00 | 1.00/1.00/1.00 |
| `harness.services.uncertainty_guard` | 4 | 1.00/0.25/0.40 | 1.00/0.50/0.67 | 1.00/0.75/0.86 |
| `harness.agent.swarm.consensus` | 4 | 0.00/0.00/0.00 | 0.00/0.00/0.00 | 0.57/1.00/0.73 |
| `harness.services.ontology_spider` | 3 | 0.00/0.00/0.00 | 0.00/0.00/0.00 | 1.00/1.00/1.00 |
| `harness.services.deep_auditor` | 2 | 0.00/0.00/0.00 | 0.00/0.00/0.00 | 0.67/1.00/0.80 |

## Edge Coverage Finding
- Unique answer-key KIs: **13**
- Gold KIs with **zero** `references_code` edges in vault: **6**
- Missing exact module-target `references_code` edges proposed for backfill: **12**
