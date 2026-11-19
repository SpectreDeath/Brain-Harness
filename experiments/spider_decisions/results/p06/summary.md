# Phase 6 — KI Retrieval Evaluation Summary

## Macro-Average Metrics Across 5 Target Modules

| Method | Precision | Recall | F1 |
|---|---:|---:|---:|
| `hop0` | 0.9600 | 1.0000 | 0.9778 |
| `hop1` | 0.7527 | 1.0000 | 0.8209 |
| `grep_baseline` | 0.8476 | 0.9500 | 0.8769 |

## Per-Module Breakdown

| Module | Gold | Hop-0 (P/R/F1) | Hop-1 (P/R/F1) | Grep Baseline (P/R/F1) |
|---|---:|---|---|---|
| `harness.services.vector_index` | 1 | 1.00/1.00/1.00 | 1.00/1.00/1.00 | 1.00/1.00/1.00 |
| `harness.services.uncertainty_guard` | 4 | 0.80/1.00/0.89 | 0.40/1.00/0.57 | 1.00/0.75/0.86 |
| `harness.agent.swarm.consensus` | 4 | 1.00/1.00/1.00 | 0.36/1.00/0.53 | 0.57/1.00/0.73 |
| `harness.services.ontology_spider` | 3 | 1.00/1.00/1.00 | 1.00/1.00/1.00 | 1.00/1.00/1.00 |
| `harness.services.deep_auditor` | 2 | 1.00/1.00/1.00 | 1.00/1.00/1.00 | 0.67/1.00/0.80 |

## Edge Coverage Finding
- Unique answer-key KIs: **13**
- Gold KIs with **zero** `references_code` edges in vault: **0**
- Missing exact module-target `references_code` edges proposed for backfill: **0**
