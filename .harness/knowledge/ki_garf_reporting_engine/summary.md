# Google Garf: Declarative SQL Reporting & Multi-Destination Data Pipeline Architecture

## Executive Architectural Summary

**Google Garf** (`google/garf`, commit `dad4209103f4a9db93ef6e32f73914cfe12fd96d`, Apache 2.0) is a multi-language reporting automation framework comprising 47,360 LOC across core Python libraries (`libs/core`, `libs/io`, `libs/executors`, `libs/actors`), Go/Rust SDKs, and Kubernetes Helm charts.

It solves the problem of brittle, procedural API reporting scripts by providing a declarative SQL-like interface that compiles queries into API parameters, normalizes nested response payloads into a structured in-memory tabular matrix (`GarfReport`), streams rows to heterogeneous analytical stores (BigQuery, DuckDB, SQLite, Sheets), and coordinates two-stage extraction/post-processing workflow DAGs.

---

## Architectural Seams & Core Abstractions

### 1. Declarative SQL Query Engine (`libs/core`)
- **`GarfQueryParser`**: Parses standard SQL `SELECT <fields> FROM <resource> [WHERE <filters>] [ORDER BY <sorts>] [LIMIT <n>]`.
- **`QueryEditor`**: Expands dynamic rolling date macros (e.g. `:YYYYMMDD-1`, `:TODAY`) and injects virtual calculated expressions.
- **Nested Field Aliasing**: Traverses nested Protobuf/JSON structures (e.g. `metrics.clicks AS clicks`) into flat tabular columns.

### 2. In-Memory Tabular Normalization (`GarfReport`)
- Decouples raw API response hierarchies from downstream consumers.
- Supports zero-copy row slicing, column-keyed dictionary projection (`to_dict_list()`), and automatic scalar coercion.

### 3. Deterministic Zero-Network Simulator (`Simulator`)
- Generates synthetic test batches matching column specifications.
- Enables reproducible unit tests, schema drift validation, and pipeline characterization without burning API quota or storing live API tokens.

### 4. Multi-Destination Analytical Egress (`libs/io`)
- **`AbsWriter`**: Unified abstraction with specialized implementations for BigQuery, DuckDB, SQLite, PostgreSQL, CSV, JSON, and Google Sheets.
- Handles atomic write transactions and batch schema synchronization.

### 5. Two-Stage Workflow DAG Execution (`libs/executors`)
- **Stage 1 (Extraction)**: Extracts reporting API slices into intermediate staging tables.
- **Stage 2 (Transformation)**: Runs analytical post-processing SQL queries inside DuckDB or BigQuery to compute derived metrics, cross-channel rollups, and anomaly metrics.
- **`ExecutionContext`**: Propagates runtime state, partition timestamps, and step metrics across DAG vertices.

---

## Decision Heuristics & Mental Models

1. **Declarative Querying over Procedural Looping**: When extracting reporting data, always declare column projections and filters in SQL. Procedural loops hardcode API client nuances and break across API version bumps.
2. **Deterministic Simulation for Gate Verification**: Never run CI/CD gates against live APIs. Use synthetic zero-network simulation to verify schemas and post-processing queries.
3. **Two-Stage Separation of Concerns**: Keep API extraction strictly partitioned from business analytical transformations. Extract raw dimensions into staging tables, then compute derived KPIs using SQL.

---

## Anti-Pattern Defenses

- **Hardcoded Absolute Dates**: Always replace static date strings with dynamic macros (`:YYYYMMDD-N`, `:TODAY`).
- **Unbounded Memory Buffering**: Enforce batch sizing and streaming writers when dealing with large result sets.
- **Direct Live Credentials in Tests**: Protect developer tokens by routing test suites through the simulation seam.
