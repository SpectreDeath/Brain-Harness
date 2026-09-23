---
name: garf-reporting-architect
description: Architect, simulate, execute, and govern declarative SQL reporting pipelines and analytical workflow DAGs across heterogeneous APIs and data stores using Google Garf patterns. Do not use for generic web scraping or OLTP transactional writes.
---

# Garf Reporting Architect: Declarative SQL API Pipelines & DAGs

`garf-reporting-architect` is the domain engineering skill for orchestrating declarative SQL-driven reporting pipelines, synthetic zero-network schema simulation, multi-destination data egress, and two-stage analytical workflow DAGs based on Google Garf patterns.

Every Garf pipeline execution follows a five-stage progression:

```
[1. Query & Macro Modeling] ──► [2. Zero-Network Simulation] ──► [3. Egress Pipeline Setup]
                                                                        │
                                                                        ▼
[5. Post-Processing SQL & Audit] ◄── [4. Workflow DAG Execution] ◄──────┘
```

See [CARD.md](CARD.md) for the companion summary card, 5-stage progression matrix, and invariants checklist.
Consult [`../data-management-architect/SKILL.md`](../data-management-architect/SKILL.md) for enterprise data governance and [`../bigquery-augmented-analytics/SKILL.md`](../bigquery-augmented-analytics/SKILL.md) for in-database analytics.

---

## 1. Query Modeling & Macro Formulation

Formulate declarative SQL queries against target reporting APIs instead of authoring brittle procedural API request scripts:

1. **Declarative Projection & Resource Selection**:
   - Write standard SQL `SELECT <fields> FROM <resource_name> WHERE <filters> LIMIT <n>`.
   - Map nested API fields to clean tabular column names using explicit aliases (e.g. `metrics.clicks AS clicks`, `campaign.id AS id`).
2. **Dynamic Date & Parameter Macro Injection**:
   - Use `:YYYYMMDD-N` or `:YYYYMMDD+N` syntax to declare dynamic rolling date intervals that evaluate at runtime.
   - Use `:TODAY` for single-day partitions.
   - Use named macro variables (e.g. `:status`, `:threshold`) to enable parameterization across execution contexts.
3. **Parse & Validate Query Syntax**:
   - Invoke `garf_parse_query(query_text, macros)` to extract the typed `GarfQuerySpec` and verify resource bounds.

> **Completion criterion**: SQL query parsed into a valid `GarfQuerySpec` with fields, filters, aliases, and macros verified.

---

## 2. Zero-Network Simulation & Schema Verification

Validate downstream pipeline schemas, field mappings, and transformation logic before touching live APIs:

1. **Deterministic Synthetic Simulation**:
   - Invoke `garf_simulate_report(query_text, row_count, seed)` to generate an in-memory `GarfReportBatch`.
   - Verify that column headers, data types, and projected aliases match target downstream table schemas.
2. **Quota & Rate-Limit Shielding**:
   - Never burn external API quotas or trigger rate limits during unit tests, schema audits, or CI/CD verification.
   - Run characterization checks and edge-case boundary audits against simulated synthetic batches.

> **Completion criterion**: Tabular report simulated deterministically and validated against target destination schemas.

---

## 3. Multi-Destination Egress Pipeline Configuration

Configure appropriate storage writers according to operational latency, volume, and analytical consumer requirements:

1. **Storage Writer Selection**:
   - **CSV (`csv`)**: Flat-file exports, archival snapshots, and external tabular consumption.
   - **JSON (`json`)**: Structured document storage, web visualization feeds, and REST payload exchange.
   - **SQLite / DuckDB (`sqlite`)**: Local analytical cache, embedded staging tables, and immediate post-processing SQL execution.
2. **Egress Execution**:
   - Invoke `garf_write_report(report_data, destination_type, destination_path)` to persist batches.
   - Inspect the returned `GarfExecutionReceipt` for row count confirmation and execution elapsed timing.

> **Completion criterion**: Report batch written to disk with verified row counts and receipt logged.

---

## 4. Two-Stage Analytical Workflow DAG Execution

Orchestrate complex extraction-transformation pipelines where API reporting queries feed into staging tables, followed by analytical SQL transformations:

1. **Step Dependency Graph Formulation**:
   - Define multi-step workflows as a directed acyclic graph (DAG) using `GarfWorkflowStep`.
   - Stage 1: API query extraction steps (`step_type: 'query'`) writing to staging destinations.
   - Stage 2: Post-processing SQL transformation steps (`step_type: 'sql'`) executing derivative metrics and rollups against staging databases.
2. **Execution Context & Parameter Passing**:
   - Pass dynamic parameters via `context_params` to share state, thresholds, and partition keys across steps.
   - Invoke `garf_run_workflow(steps, context_params)` to execute the DAG in topological order.

> **Completion criterion**: All DAG steps executed without cyclic deadlocks and execution receipt logged.

---

## 5. Post-Processing SQL Transformation & Telemetry Audit

Finalize data products by computing derived KPIs and conducting structural telemetry audits:

1. **Analytical Post-Processing Queries**:
   - Run SQL aggregation queries on the staging database (e.g. calculating Cost Per Acquisition, CTR anomalies, or channel share).
   - Create curated views and materialized summary tables for downstream dashboard or model consumption.
2. **Verification & Audit Seams**:
   - Verify table row counts against initial extraction receipts.
   - Check data freshness and log pipeline metrics via standard telemetry channels.

> **Completion criterion**: Post-processed analytical tables verified and pipeline audit complete.

---

## Diagnostic Coaching Scorecard

| Diagnostic Check | Evaluation Criterion | Pass Condition |
| :--- | :--- | :--- |
| **Declarative SQL Syntax** | Does the query use standard SQL clauses (`SELECT`, `FROM`, `WHERE`)? | Query parses cleanly via `garf_parse_query` |
| **Alias Completeness** | Are all nested API fields aliased to flat tabular column names? | `column_names` contains clean snake_case identifiers |
| **Date Macro Correctness** | Are dynamic date windows expressed using `:YYYYMMDD-N` or `:TODAY`? | Macros expanded into ISO date literals |
| **Zero-Network Verification** | Was the pipeline tested using simulated data before live API calls? | Unit test executes without network calls |
| **DAG Dependency Safety** | Are workflow step dependencies acyclic and correctly ordered? | Topological sort succeeds without cycles |

---

## Anti-Patterns

- **Ad-Hoc Endpoint Hardcoding** — Writing manual HTTP requests and JSON parsing loops instead of compiling declarative SQL queries over reporting APIs.
- **Quota-Burning Unit Tests** — Invoking live production APIs during test suites instead of utilizing deterministic synthetic simulation.
- **Unbounded In-Memory Slicing** — Loading multi-gigabyte query responses into memory without streaming writers or row batch limits.
- **Monolithic Script Sprawl** — Interleaving data fetching, file writing, and statistical calculations into a single opaque script instead of partitioning into a two-stage DAG.
- **Unpinned Date Literals** — Hardcoding static date strings (`2026-01-01`) into recurring reporting pipelines rather than dynamic `:YYYYMMDD-N` macros.
