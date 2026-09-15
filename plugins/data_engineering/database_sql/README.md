# plugin.database_sql (v1.0.0)

Universal SQL database schema inspector, query runner, and execution plan explainer

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/data_engineering/database_sql` |
| Category | `data_engineering` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `sql_inspect_schema` | `(db_path)` | Inspect all tables, columns, data types, primary keys, and row counts in a SQLite database |
| `sql_execute_query` | `(query, db_path, read_only, limit)` | Execute a SQL query with read-only safety validation and result limits |
| `sql_explain_query` | `(query, db_path)` | Get query execution plan (EXPLAIN QUERY PLAN) for a SQL statement |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

SQL database schema introspection and query execution plugin for Brain Harness.

#### Functions

- `def sql_inspect_schema(db_path) -> dict[str, Any]` — Inspect all tables, column schemas, types, and counts in a SQLite database.
- `def sql_execute_query(query, db_path, read_only, limit) -> dict[str, Any]` — Execute a SQL query with read-only validation and pagination.
- `def sql_explain_query(query, db_path) -> dict[str, Any]` — Explain execution plan for a SQL query.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.data_engineering.database_sql.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
