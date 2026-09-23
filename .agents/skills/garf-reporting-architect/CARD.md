```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: garf-reporting-architect                                      │
│ Category: data_engineering / analytics                              │
│ Version: 1.0.0                                                       │
│ Invocation: /garf-reporting-architect                                │
│ Triggers: "garf reporting", "declarative sql api", "api query dag",   │
│           "report simulation", "analytical workflow dag"             │
│ Requires: "garf_reporting_pipeline", "bigquery_augmented_analytics"  │
│ Target: Declarative SQL reporting pipelines, simulation & DAGs       │
└──────────────────────────────────────────────────────────────────────┘
```

# Garf Reporting Architect — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Query Modeling** | Formulate declarative SQL query with aliases & macros | `GarfQuerySpec` | Standard SQL parsed & dynamic macros evaluated |
| **Stage 2: Simulation** | Deterministically simulate synthetic tabular report | `GarfReportBatch` | Schema verified without live API network calls |
| **Stage 3: Egress Pipeline** | Write report batch to CSV, JSON, or SQLite | `GarfExecutionReceipt` | Egress persistence confirmed with row counts |
| **Stage 4: Workflow DAG** | Execute multi-step query & post-processing DAG | `GarfExecutionReceipt` | Steps topologically resolved & executed |
| **Stage 5: Post-Processing** | Execute analytical SQL transformations & telemetry | Curated Data Products | Derived metrics materialized & audit logged |

---

## Vocabulary & Levers

- **Declarative SQL API Interface**: Compiling SQL `SELECT ... FROM ... WHERE ...` syntax into reporting API query parameters.
- **Dynamic Date Macros**: In-query `:YYYYMMDD-N` expressions resolving rolling date windows at runtime.
- **Zero-Network Simulation**: Generating synthetic test batches matching column definitions to validate downstream schemas without API quotas.
- **Two-Stage Analytical DAG**: Pattern where API query extracts stage data into local/remote tables, followed by analytical SQL post-processing.
- **Tabular Egress Pipeline**: Streaming in-memory report matrices directly to CSV, JSON, SQLite, or BigQuery.

---

## Mandatory Invariants Checklist

- [ ] **Declarative over Imperative**: Always author declarative SQL queries instead of procedural HTTP fetching loops.
- [ ] **Zero-Network Testing**: Verify pipeline schemas against simulated batches before hitting live APIs.
- [ ] **Slotted & Frozen Dataclasses**: All internal reporting data entities must declare `slots=True, frozen=True` (Rule 12).
- [ ] **Acyclic DAG Dependencies**: Verify that workflow steps have valid, non-cyclic dependency graphs.
- [ ] **Dual-File Knowledge Vault**: Persist architectural claims in canonical `metadata.json` + `summary.md` format (Rule 40).
