# Skill Summary Card: `bigquery-augmented-analytics`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:       bigquery-augmented-analytics              │
│ Category:    data_engineering / augmented_analytics    │
│ Invocation:  /bigquery-augmented-analytics             │
│ Trigger:     "diagnose why metric changed in BigQuery",│
│              "BigQuery augmented analytics",           │
│              "AI.KEY_DRIVERS", "AI.CAUSAL_EFFECT",     │
│              "ML.DETECT_CHANGE_POINTS", "ML.TREND",    │
│              "detect change points", "causal lift SQL" │
│ Version:     1.0.0                                     │
│ Provides:    "in_database_augmented_analytics"         │
├────────────────────────────────────────────────────────┤
│ Target:      Execute in-database AI/ML TVFs to detect  │
│              anomalies, attribute multi-dimensional    │
│              drivers, and estimate causal lift.        │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Literature Synthesis Loop

| Stage | Objective | SQL TVF / Mechanism | Completion Gate |
|---|---|---|---|
| **1. Temporal Profiling** | Isolate trend slope from noise & cyclical calendar patterns | `ML.TREND`, `ML.SEASONALITY` | Trend & seasonal periodicity isolated; noise filtered |
| **2. Shift Isolation** | Detect statistically significant step changes in time series | `ML.DETECT_CHANGE_POINTS` | Shift timestamp $t_0$ isolated with prob $\ge 95\%$ |
| **3. Combinatorial Attribution** | Scan multi-dimensional segments explaining cohort delta | `AI.KEY_DRIVERS`, `ML.CORRELATION` | Reference vs interest cohort variance decomposed |
| **4. Counterfactual Lift** | Model synthetic control baseline via `ARIMA_PLUS` | `AI.CAUSAL_EFFECT` | True causal lift calculated over organic growth |
| **5. Executive Synthesis** | Formulate 4-point diagnostic root-cause narrative | Executive Diagnostic Brief | Business impact & recommendations delivered |

---

## The Three Pillars Cheat Sheet

### 1. The Visual Brief (Temp HTML + Mermaid)
```html
<!-- Location: %TEMP%\bigquery-augmented-analytics-<timestamp>.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>
</head>
<body class="bg-[#0d1117] text-[#c9d1d9] p-8 max-w-6xl mx-auto">
  <!-- Investigative Chaining DAG & Diagnostic Scorecards -->
</body>
</html>
```

### 2. The Mandatory Checkpoint (`RequestFeedback: true`)
```markdown
# Implementation Plan
Set `RequestFeedback: true` in artifact metadata.
Agent MUST STOP and wait for explicit user approval before executing large BigQuery TVF scans.
```

### 3. Explicit Anti-Patterns Box
- **The Data Egress Tax**: Pulling raw rows into pandas/R instead of executing in-engine SQL TVFs.
- **Fluctuation Hallucination**: Treating seasonal patterns as change points without running `ML.TREND`.
- **Naive Pre/Post Attribution**: Ignoring organic baseline growth instead of using `AI.CAUSAL_EFFECT`.
- **Unparameterized Date Hardcoding**: Guessing date cuts instead of piping `ML.DETECT_CHANGE_POINTS`.
- **Micro-Segment Noise Flooding**: Forgetting `min_apriori_support` pruning on high-cardinality features.

---

## Verification & Quality Checklist

- [ ] **Zero Data Egress**: All analytical workloads execute directly via BigQuery SQL TVFs.
- [ ] **Dynamic Chaining**: Outputs of `ML.DETECT_CHANGE_POINTS` directly parameterize `AI.KEY_DRIVERS`.
- [ ] **Counterfactual Baseline**: Causal lift is validated against `ARIMA_PLUS` projections.
- [ ] **Pruned Cardinality**: Apriori support $\ge 0.01$ to prevent spurious micro-segment attribution.
- [ ] **Companion Card Co-Located**: Co-located `CARD.md` authored with single-pipe ASCII border.
- [ ] **Craft Standard Verified**: Passes `harness skills validate` with zero warnings.
