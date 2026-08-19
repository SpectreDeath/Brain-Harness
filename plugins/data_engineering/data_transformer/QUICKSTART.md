# Quick Start Guide: `plugin.data_transformer` (v1.0.0)

> Multi-format data converter (JSON ↔ CSV ↔ YAML ↔ TOML), tabular filter, and statistical profiler

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`data_convert_format`**: Convert structured data between JSON, CSV, YAML, and TOML formats
- **`data_filter_table`**: Filter, sort, and slice a list of dictionary records
- **`data_summarize_stats`**: Compute statistical metrics (count, mean, min, max, nulls, unique count) for columns in tabular data
- **`data_validate_schema`**: Validate a dictionary against expected types and required field schema

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('plugin.data_transformer.data_convert_format', {'content': '<content>', 'from_format': '<from_format>', 'to_format': '<to_format>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider plugin.data_transformer
harness plugin enable plugin.data_transformer
```

## ⚡ Available Entrypoints & Skills
- **`data_convert_format(content: string, from_format: string, to_format: string)`**
  Convert structured data between JSON, CSV, YAML, and TOML formats
- **`data_filter_table(records: array, filters: object, sort_by: string, descending: boolean, limit: integer)`**
  Filter, sort, and slice a list of dictionary records
- **`data_summarize_stats(records: array, columns: array)`**
  Compute statistical metrics (count, mean, min, max, nulls, unique count) for columns in tabular data
- **`data_validate_schema(data: object, schema: object)`**
  Validate a dictionary against expected types and required field schema