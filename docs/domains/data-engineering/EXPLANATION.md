# Data Engineering Domain Architecture

The Data Engineering domain governs curated tabular dataset acquisition, out-of-core statistical moment profiling, schema transformation, and relational database execution.

---

## Domain Scope & Boundaries

This domain handles structured data ingestion, analytical profiling, and data transformations:
- **In Scope**: Curated tabular datasets (UCI, Kaggle, OpenData), out-of-core statistical profiling, schema reshaping, time-to-event survival models, and BigQuery TVF causal analytics.
- **Out of Scope**: Unstructured web scraping without schemas (Integration & I/O), raw NLP embedding vector caches (Memory & Epistemics), or ad-hoc file editing.

---

## Ubiquitous Language & Core Terminology

- **Topology Profile**: A compact, out-of-core statistical fingerprint capturing moments, null ratios, and outlier contamination without loading raw rows into context. (*Avoid*: Data summary, table stats, EDA dump)
- **Curated Pipeline**: A direct ingestion path targeting standardized tabular repositories (UCI, Kaggle, OpenData) that eliminates unstructured scraping. (*Avoid*: Data scraper, downloader, fetcher)
- **Transformer**: A deterministic schema reshaping and column normalization pipeline converting raw inputs into memory-efficient columnar formats. (*Avoid*: Cleaner, converter, sanitizer)
- **Synthetic Matrix**: An artificially generated tabular dataset preserving target statistical distributions and correlation structures for benchmarking. (*Avoid*: Fake data, mock table, dummy data)
- **Time-to-Event Model**: A semiparametric or nonparametric statistical model (Cox PH, Kaplan-Meier) analyzing duration until a binary event under right-censoring. (*Avoid*: Survival calculator, churn predictor, failure timer)
- **Data Topology Map**: A formal graph representation of data structures, causal DAG lineages, and execution queues across system boundaries. (*Avoid*: Data flow diagram, schema map, entity relationship chart)

---

## Architectural Invariants & Patterns

- **Out-of-Core Memory Boundaries**: Tabular datasets exceeding context bounds must use zero-copy Arrow memory mapping or streaming iterators (`HfDatasetsService`).
- **Data Topology Mapping Before Mutation**: Domain models, schemas, and execution queues must be formally mapped prior to structural code modifications to prevent regression.
- **Stateless Scientific Isolation (Rule 24)**: Heavy simulation models and parameter solvers are encapsulated behind Model Context Protocol (MCP) servers.

---

## Co-Located Plugins & Micro-Kernel Services

- **Data Management Service**: [`src/harness/services/data_management.py`](../../../src/harness/services/data_management.py) providing `DataManagementService`.
- **BigQuery Augmented Analytics**: [`src/harness/services/bigquery_augmented_analytics.py`](../../../src/harness/services/bigquery_augmented_analytics.py) providing `BIGQUERY_AUGMENTED_ANALYTICS_SERVICE_KEY`.
- **HF Datasets Service**: [`src/harness/services/hf_datasets.py`](../../../src/harness/services/hf_datasets.py) providing `HF_DATASETS_SERVICE_KEY`.
- **Garf Reporting Service**: [`src/harness/services/garf_reporting.py`](../../../src/harness/services/garf_reporting.py) providing `GARF_REPORTING_SERVICE_KEY`.
- **Open-Source GIS Service**: [`src/harness/services/open_source_gis.py`](../../../src/harness/services/open_source_gis.py) providing `OPEN_SOURCE_GIS_SERVICE_KEY`.

---

## Associated Agent Skills

- [`structured-data-scout`](../../../.agents/skills/structured-data-scout/SKILL.md): Discovers and downloads clean tabular data products.
- [`data-topology-mapper`](../../../.agents/skills/data-topology-mapper/SKILL.md): Formulates formal DAG lineages and schema topology maps.
- [`bigquery-augmented-analytics`](../../../.agents/skills/bigquery-augmented-analytics/SKILL.md): Executes in-database TVFs and ARIMA_PLUS counterfactual causal inference.
- [`survival-analysis`](../../../.agents/skills/survival-analysis/SKILL.md): Estimates survival curves, Cox PH regression, and Schoenfeld residuals.
