"""SQL database schema introspection and query execution plugin for Brain Harness."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any


def _get_connection(db_path: str) -> sqlite3.Connection:
    """Open a SQLite database connection with row factory."""
    p = Path(db_path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    return conn


def sql_inspect_schema(db_path: str = ".harness/storage.db") -> dict[str, Any]:
    """Inspect all tables, column schemas, types, and counts in a SQLite database."""
    try:
        conn = _get_connection(db_path)
        cursor = conn.cursor()

        # Fetch all user tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row["name"] for row in cursor.fetchall()]

        schema_report: list[dict[str, Any]] = []
        for tbl in sorted(tables):
            cursor.execute(f"PRAGMA table_info('{tbl}');")
            columns = [
                {
                    "name": col["name"],
                    "type": col["type"] or "TEXT",
                    "not_null": bool(col["notnull"]),
                    "primary_key": bool(col["pk"]),
                }
                for col in cursor.fetchall()
            ]

            try:
                cursor.execute(f"SELECT count(*) as cnt FROM '{tbl}';")
                count_row = cursor.fetchone()
                row_count = count_row["cnt"] if count_row else 0
            except Exception:
                row_count = 0

            schema_report.append({
                "table_name": tbl,
                "row_count": row_count,
                "columns_count": len(columns),
                "columns": columns,
            })

        conn.close()
        return {
            "status": "ok",
            "db_path": db_path,
            "tables_count": len(schema_report),
            "tables": schema_report,
        }
    except Exception as e:
        return {"status": "error", "error": f"Schema inspection failed: {e!s}"}


def sql_execute_query(
    query: str,
    db_path: str = ".harness/storage.db",
    read_only: bool = True,
    limit: int = 50,
) -> dict[str, Any]:
    """Execute a SQL query with read-only validation and pagination."""
    try:
        cleaned_query = query.strip()
        if not cleaned_query:
            return {"status": "error", "error": "Query cannot be empty."}

        # Read-only guard
        if read_only:
            first_word = cleaned_query.split()[0].upper()
            if first_word not in ("SELECT", "PRAGMA", "EXPLAIN", "WITH"):
                return {
                    "status": "error",
                    "error": f"Write query '{first_word}' rejected. Set read_only=false to execute write queries.",
                }
            if re.search(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|VACUUM)\b", cleaned_query, re.IGNORECASE):
                return {
                    "status": "error",
                    "error": "Destructive or write SQL statements are blocked in read-only mode.",
                }

        conn = _get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(cleaned_query)

        if cursor.description is not None:
            # Query returned tabular data
            headers = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchmany(limit)
            rows = [dict(zip(headers, [r[h] for h in headers], strict=False)) for r in raw_rows]
            conn.close()
            return {
                "status": "ok",
                "query": query,
                "rows_count": len(rows),
                "columns": headers,
                "rows": rows,
            }
        else:
            # DDL or DML statement
            rowcount = cursor.rowcount
            conn.commit()
            conn.close()
            return {
                "status": "ok",
                "query": query,
                "affected_rows": rowcount,
            }
    except Exception as e:
        return {"status": "error", "error": f"Query execution failed: {e!s}"}


def sql_explain_query(
    query: str,
    db_path: str = ".harness/storage.db",
) -> dict[str, Any]:
    """Explain execution plan for a SQL query."""
    try:
        conn = _get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(f"EXPLAIN QUERY PLAN {query}")

        plan_steps = []
        for row in cursor.fetchall():
            plan_steps.append({
                "id": row[0],
                "parent": row[1],
                "detail": row[3] if len(row) > 3 else str(row[2]),
            })

        conn.close()
        return {
            "status": "ok",
            "query": query,
            "plan_steps_count": len(plan_steps),
            "plan": plan_steps,
        }
    except Exception as e:
        return {"status": "error", "error": f"EXPLAIN failed: {e!s}"}
