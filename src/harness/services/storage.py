"""Storage service plugin — key-value and document storage interface.

Provides persistent storage that other plugins can use for state,
configuration, and data. Ships with a SQLite-backed implementation.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger()



class IsnadLineageNode(BaseModel):
    """Lineage node representing a primary source, test receipt, or manifest."""

    node_type: str = Field(..., description="Node category: primary_code, verification_test, manifest, tool_event")
    uri: str = Field(..., description="File path, URL, or identifier with line slice (e.g. file:///...#L10-L20)")
    sha256_hash: str | None = Field(default=None, description="SHA-256 hash of node content")
    verified: bool = Field(default=False, description="Whether node has been verified against ground truth")


class IsnadLineageBlock(BaseModel):
    """Complete Isnad chain-of-custody block verifying architectural claims."""

    decision_id: str = Field(..., description="Unique decision or learning identifier")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO timestamp")
    claims: list[dict[str, Any]] = Field(default_factory=list, description="Audited assertions and provenance nodes")
    status: str = Field(default="VERIFIED", description="Lineage status: VERIFIED, HYPOTHESIS, REJECTED")


class KnowledgeItemRecord(BaseModel):
    """Ground-truth Knowledge Item (KI) extracted from brains, repos, or audits."""

    id: str = Field(..., description="Unique KI identifier (e.g. ki_20260822_01)")
    title: str = Field(..., description="Actionable heuristic or pattern title")
    source_target: str = Field(..., description="Origin folder path, Git URL, or brain URI")
    detected_format: str = Field(..., description="Format signature: antigravity_brain, git_repository, ide_memo, etc.")
    isnad: IsnadLineageBlock | dict[str, Any] = Field(default_factory=dict, description="Chain of custody provenance")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")
    summary: str = Field(default="", description="Operational guideline and implementation details")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class StorageService(ABC):
    """Abstract storage interface for plugins.

    Provides key-value, document-style, and knowledge-item operations.
    """

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get a value by key. Returns None if not found."""

    @abstractmethod
    async def set(self, key: str, value: Any) -> None:
        """Set a value by key."""

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a key. Returns True if the key existed."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists."""

    @abstractmethod
    async def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys, optionally filtered by prefix."""

    @abstractmethod
    async def clear(self) -> int:
        """Delete all keys. Returns the number of keys deleted."""

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        """Get multiple values by key. Returns a mapping of existing keys to values."""
        result: dict[str, Any] = {}
        for key in keys:
            val = await self.get(key)
            if val is not None:
                result[key] = val
        return result

    async def set_many(self, mapping: dict[str, Any]) -> None:
        """Set multiple key-value pairs."""
        for key, val in mapping.items():
            await self.set(key, val)

    async def get_all(self, prefix: str = "") -> dict[str, Any]:
        """Retrieve all key-value pairs matching an optional prefix."""
        keys = await self.list_keys(prefix=prefix)
        return await self.get_many(keys)

    async def delete_many(self, keys: list[str]) -> int:
        """Delete multiple keys. Returns the number of keys deleted."""
        deleted = 0
        for key in keys:
            if await self.delete(key):
                deleted += 1
        return deleted

    async def save_knowledge_item(self, item: KnowledgeItemRecord) -> None:
        """Save a Knowledge Item record under the canonical knowledge prefix."""
        payload = item.model_dump()
        await self.set(f"ki:{item.id}", payload)

    async def get_knowledge_item(self, ki_id: str) -> KnowledgeItemRecord | None:
        """Retrieve a Knowledge Item by its ID."""
        raw = await self.get(f"ki:{ki_id}")
        if raw is None:
            return None
        return KnowledgeItemRecord.model_validate(raw)

    async def list_knowledge_items(self, tag: str | None = None) -> list[KnowledgeItemRecord]:
        """List all Knowledge Items, optionally filtered by tag."""
        records = await self.get_all(prefix="ki:")
        items: list[KnowledgeItemRecord] = []
        for val in records.values():
            try:
                ki = KnowledgeItemRecord.model_validate(val)
                if tag is None or tag in ki.tags:
                    items.append(ki)
            except Exception as e:
                logger.warning("Failed to validate knowledge item", error=str(e))
        return items

    def compute_sha256(self, content: str | bytes) -> str:
        """Compute SHA-256 hash for provenance nodes."""
        data = content.encode("utf-8") if isinstance(content, str) else content
        return hashlib.sha256(data).hexdigest()


# Canonical service key for storage
STORAGE_SERVICE_KEY: ServiceKey[StorageService] = ServiceKey("storage.default")


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
            self._conn = sqlite3.connect(self._db_path)
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
        except json.JSONDecodeError:
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
            except json.JSONDecodeError:
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
            except json.JSONDecodeError:
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


class StoragePlugin(HarnessPlugin):
    """Built-in plugin that provides the storage service."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self._db_path = db_path
        self._service: SQLiteStorageService | None = None

    @property
    def name(self) -> str:
        return "storage.sqlite"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "SQLite-backed key-value storage service"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [STORAGE_SERVICE_KEY]

    @property
    def trusted(self) -> bool:
        return True

    async def on_load(self, ctx: ServiceContext) -> None:
        db_path = self._db_path or Path.home() / ".harness" / "storage.db"
        if isinstance(db_path, Path):
            db_path.parent.mkdir(parents=True, exist_ok=True)
        self._service = SQLiteStorageService(db_path)
        ctx.provide(STORAGE_SERVICE_KEY, self._service, provider=self.name)
        logger.info("Storage service registered", db_path=str(db_path))

    async def on_unload(self) -> None:
        if self._service:
            self._service.close()
            self._service = None
