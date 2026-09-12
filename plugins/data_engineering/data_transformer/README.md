# plugin.data_transformer (v1.0.0)

Multi-format data converter (JSON ↔ CSV ↔ YAML ↔ TOML), tabular filter, and statistical profiler

---

## Overview & Metadata

- **Plugin Directory**: `plugins/data_engineering/data_transformer`
- **Isolation Mode**: `in_process`
- **Services Provided**: None
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `data_convert_format` | `(content, from_format, to_format)` | Convert structured data between JSON, CSV, YAML, and TOML formats |
| `data_filter_table` | `(records, filters, sort_by, descending, limit)` | Filter, sort, and slice a list of dictionary records |
| `data_summarize_stats` | `(records, columns)` | Compute statistical metrics (count, mean, min, max, nulls, unique count) for columns in tabular data |
| `data_validate_schema` | `(data, schema)` | Validate a dictionary against expected types and required field schema |

---

## Key Modules & AST Symbols

### Module [`main.py`](main.py)

#### Functions

- `def data_convert_format(content, from_format, to_format) -> dict[str, Any]`
  - Convert structured data between JSON, CSV, and TOML.
- `def data_filter_table(records, filters, sort_by, descending, limit) -> dict[str, Any]`
  - Filter, sort, and slice tabular records.
- `def data_summarize_stats(records, columns) -> dict[str, Any]`
  - Compute statistical summaries for table columns.
- `def data_validate_schema(data, schema) -> dict[str, Any]`
  - Validate a dictionary against expected field types and presence.



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
