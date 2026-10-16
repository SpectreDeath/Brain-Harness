# plugin.garf_reporting_pipeline (v1.0.0)

Google Garf declarative SQL reporting, synthetic simulation, multi-destination data pipeline, and workflow DAG execution bridge

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/data_engineering/garf_reporting_pipeline` |
| Category | `data_engineering` |
| Isolation Mode | `subprocess` |
| Services Provided | `data_engineering.garf_reporting` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `garf_parse_query` | `(query_text, macros)` | Parse a reporting API SQL query into structured components (fields, aliases, filters, sorts, limit, dynamic macros) |
| `garf_simulate_report` | `(query_text, row_count, seed)` | Deterministically simulate a tabular report matching SQL query specifications without live network API calls |
| `garf_write_report` | `(report_data, destination_type, destination_path)` | Write a tabular report batch to target storage (CSV, JSON, SQLite, Console) |
| `garf_execute_query` | `(query_text, destination_type, destination_path, macros)` | End-to-end execution: parses query, simulates/fetches report, and optionally writes to target destination |
| `garf_run_workflow` | `(steps, context_params)` | Execute a multi-step analytical workflow DAG orchestrating API data queries and SQL post-processing |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Google Garf declarative SQL reporting, synthetic simulation, multi-destination data pipeline, and workflow DAG execution bridge

#### Classes

- `class GarfReportingPlugin` — Harness Plugin implementing Google Garf declarative SQL reporting.
  - `def __init__()` — Executes the operation.
  - `def provides()` — Executes the operation.
  - `def on_load(context)` — Executes the operation.
  - `def on_unload(context)` — Executes the operation.
  - `def parse_query(query_text, macros)` — Parse a reporting API SQL query into structured components.
  - `def simulate_report(query_spec, row_count, seed)` — Deterministically simulate a tabular report matching query column specs.
  - `def write_report(report, destination_type, destination_path)` — Write tabular report batch to target storage (CSV, JSON, SQLite).
  - `def execute_query(query_text, destination_type, destination_path, macros)` — End-to-end execute query: parse, simulate/fetch, and optionally write.
  - `def run_workflow(steps, context_params)` — Execute a multi-step analytical workflow DAG.

---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.data_engineering.garf_reporting_pipeline.main import plugin

context = ServiceContext()
# Load plugin into service context
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `subprocess` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
