# Quick Start Guide: `plugin.database_sql` (v1.0.0)

> Universal SQL database schema inspector, query runner, and execution plan explainer

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`sql_inspect_schema`**: Inspect all tables, columns, data types, primary keys, and row counts in a SQLite database
- **`sql_execute_query`**: Execute a SQL query with read-only safety validation and result limits
- **`sql_explain_query`**: Get query execution plan (EXPLAIN QUERY PLAN) for a SQL statement

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('plugin.database_sql.sql_inspect_schema', {'db_path': '<db_path>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider plugin.database_sql
harness plugin enable plugin.database_sql
```

## ⚡ Available Entrypoints & Skills
- **`sql_inspect_schema(db_path: string)`**
  Inspect all tables, columns, data types, primary keys, and row counts in a SQLite database
- **`sql_execute_query(query: string, db_path: string, read_only: boolean, limit: integer)`**
  Execute a SQL query with read-only safety validation and result limits
- **`sql_explain_query(query: string, db_path: string)`**
  Get query execution plan (EXPLAIN QUERY PLAN) for a SQL statement