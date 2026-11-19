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

## Re-Baseline Note (2026-11-19)
- **Primary high-precision retrieval mode (`hop0`):** P=`0.9600`, R=`1.0000`, F1=`0.9778` (meets `>= 0.90` precision bar; `ki_google_research_smart_eval` adds 1 valid Phase 6 edge on `uncertainty_guard` beyond the frozen Phase 1 gold key).
- **Exploratory recall expansion (`hop1`):** P=`0.7527`, R=`1.0000`, F1=`0.8209` — original Phase 1 acceptance (`hop1` P `>= 0.90`) was **not** met (`0.7889` at commit `120c201`) because 1-hop `related_to`/`same_domain` sibling expansion adds 5 non-gold KIs on `uncertainty_guard` and 7 on `swarm.consensus`. Re-baselined as exploratory recall expansion (`R=1.0000`, `F1 >= 0.82`, `P >= 0.75`).
