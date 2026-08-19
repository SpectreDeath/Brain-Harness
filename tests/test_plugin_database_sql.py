"""Tests for database_sql plugin."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from plugins.data_engineering.database_sql.main import (
    sql_execute_query,
    sql_explain_query,
    sql_inspect_schema,
)


@pytest.mark.unit
class TestDatabaseSqlPlugin:
    @pytest.fixture
    def sample_db(self, tmp_path: Path) -> str:
        db_file = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_file))
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE);")
        conn.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, FOREIGN KEY(user_id) REFERENCES users(id));")
        conn.execute("INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com'), ('Bob', 'bob@example.com');")
        conn.execute("INSERT INTO posts (user_id, title) VALUES (1, 'Hello World'), (1, 'Second Post');")
        conn.commit()
        conn.close()
        return str(db_file)

    def test_sql_inspect_schema(self, sample_db: str) -> None:
        res = sql_inspect_schema(sample_db)
        assert res["status"] == "ok"
        assert res["tables_count"] == 2

        tables = {t["table_name"]: t for t in res["tables"]}
        assert "users" in tables
        assert "posts" in tables
        assert tables["users"]["row_count"] == 2
        assert len(tables["users"]["columns"]) == 3

    def test_sql_execute_select(self, sample_db: str) -> None:
        res = sql_execute_query("SELECT id, name, email FROM users ORDER BY id ASC;", db_path=sample_db)
        assert res["status"] == "ok"
        assert res["rows_count"] == 2
        assert res["rows"][0]["name"] == "Alice"
        assert res["rows"][1]["name"] == "Bob"

    def test_sql_execute_write_blocked_in_readonly(self, sample_db: str) -> None:
        res = sql_execute_query("DELETE FROM users WHERE id = 1;", db_path=sample_db, read_only=True)
        assert res["status"] == "error"
        assert "rejected" in res["error"] or "blocked" in res["error"]

    def test_sql_execute_write_allowed(self, sample_db: str) -> None:
        res = sql_execute_query("INSERT INTO users (name, email) VALUES ('Charlie', 'charlie@example.com');", db_path=sample_db, read_only=False)
        assert res["status"] == "ok"
        assert res["affected_rows"] == 1

        # Verify insertion
        res_verify = sql_execute_query("SELECT count(*) as count FROM users;", db_path=sample_db)
        assert res_verify["rows"][0]["count"] == 3

    def test_sql_explain_query(self, sample_db: str) -> None:
        res = sql_explain_query("SELECT * FROM users WHERE email = 'alice@example.com';", db_path=sample_db)
        assert res["status"] == "ok"
        assert res["plan_steps_count"] >= 1
