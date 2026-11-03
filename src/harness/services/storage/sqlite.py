"""SQLite-backed key-value and document storage implementation."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any

from harness.services.storage.protocols import StorageService


class SQLiteStorageService(StorageService):
    """SQLite-backed storage service.

    Stores values as JSON-serialized strings in a simple key-value table.
    Thread-safe via SQLite's built-in locking.
    """

    def __init__(self, db_path: Path | str = ":memory:") -> None:
        self._db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None

    def _ensure_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS kv_store (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self._conn.commit()
        return self._conn

    async def get(self, key: str) -> Any | None:
        conn = self._ensure_connection()
        cursor = conn.execute("SELECT value FROM kv_store WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row is None:
            return None
        try:
            return json.loads(row[0])
        except json.JSONDecodeError as ex:
            logger.warning("Corrupt JSON payload in kv_store, returning raw string", key=key, error=str(ex))
            return row[0]

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        if not keys:
            return {}
        conn = self._ensure_connection()
        placeholders = ",".join("?" for _ in keys)
        cursor = conn.execute(
            f"SELECT key, value FROM kv_store WHERE key IN ({placeholders})",
            keys,
        )
        result: dict[str, Any] = {}
        for key, val_str in cursor.fetchall():
            try:
                result[key] = json.loads(val_str)
            except json.JSONDecodeError as ex:
                logger.warning("Corrupt JSON payload in kv_store get_many, returning raw string", key=key, error=str(ex))
                result[key] = val_str
        return result

    async def set(self, key: str, value: Any) -> None:
        conn = self._ensure_connection()
        serialized = json.dumps(value)
        conn.execute(
            """
            INSERT INTO kv_store (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, serialized),
        )
        conn.commit()

    async def set_many(self, mapping: dict[str, Any]) -> None:
        if not mapping:
            return
        conn = self._ensure_connection()
        records = [(k, json.dumps(v)) for k, v in mapping.items()]
        conn.executemany(
            """
            INSERT INTO kv_store (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            records,
        )
        conn.commit()

    async def get_all(self, prefix: str = "") -> dict[str, Any]:
        conn = self._ensure_connection()
        if prefix:
            cursor = conn.execute(
                "SELECT key, value FROM kv_store WHERE key LIKE ? ORDER BY key",
                (f"{prefix}%",),
            )
        else:
            cursor = conn.execute("SELECT key, value FROM kv_store ORDER BY key")
        result: dict[str, Any] = {}
        for key, val_str in cursor.fetchall():
            try:
                result[key] = json.loads(val_str)
            except json.JSONDecodeError as ex:
                logger.warning("Corrupt JSON payload in kv_store get_many, returning raw string", key=key, error=str(ex))
                result[key] = val_str
        return result

    async def delete(self, key: str) -> bool:
        conn = self._ensure_connection()
        cursor = conn.execute("DELETE FROM kv_store WHERE key = ?", (key,))
        conn.commit()
        return cursor.rowcount > 0

    async def delete_many(self, keys: list[str]) -> int:
        if not keys:
            return 0
        conn = self._ensure_connection()
        placeholders = ",".join("?" for _ in keys)
        cursor = conn.execute(
            f"DELETE FROM kv_store WHERE key IN ({placeholders})",
            keys,
        )
        conn.commit()
        return cursor.rowcount

    async def exists(self, key: str) -> bool:
        conn = self._ensure_connection()
        cursor = conn.execute("SELECT 1 FROM kv_store WHERE key = ?", (key,))
        return cursor.fetchone() is not None

    async def list_keys(self, prefix: str = "") -> list[str]:
        conn = self._ensure_connection()
        if prefix:
            cursor = conn.execute(
                "SELECT key FROM kv_store WHERE key LIKE ? ORDER BY key",
                (f"{prefix}%",),
            )
        else:
            cursor = conn.execute("SELECT key FROM kv_store ORDER BY key")
        return [row[0] for row in cursor.fetchall()]

    async def clear(self) -> int:
        conn = self._ensure_connection()
        cursor = conn.execute("SELECT COUNT(*) FROM kv_store")
        count = int(cursor.fetchone()[0])
        conn.execute("DELETE FROM kv_store")
        conn.commit()
        return count

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def sync_ki_edges(self, graph: Any) -> int:
        """Sync asserted and derived edges from graph topology into ki_edges table."""
        from harness.services.storage.vault_sqlite_graph import sync_ki_edges as _sync_edges

        return _sync_edges(self._ensure_connection(), graph)

    def find_path_sql(
        self,
        from_id: str,
        to_id: str,
        max_depth: int = 6,
        exclude_derived: bool = False,
        directed: bool = False,
    ) -> dict[str, Any]:
        """Find cycle-safe shortest path between two nodes using SQLite WITH RECURSIVE CTE."""
        from harness.services.storage.vault_sqlite_graph import find_path_sql as _find_path

        return _find_path(
            self._ensure_connection(),
            from_id,
            to_id,
            max_depth=max_depth,
            exclude_derived=exclude_derived,
            directed=directed,
        )

    def get_transitive_dependents_sql(
        self,
        target_id: str,
        max_depth: int = 6,
    ) -> list[dict[str, Any]]:
        """Retrieve multi-hop inbound dependents using SQLite WITH RECURSIVE CTE."""
        from harness.services.storage.vault_sqlite_graph import get_transitive_dependents_sql as _get_dep

        return _get_dep(self._ensure_connection(), target_id, max_depth=max_depth)
