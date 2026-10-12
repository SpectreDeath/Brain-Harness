"""Storage service plugin registration and lifecycle."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.storage.protocols import (
    KNOWLEDGE_VAULT_KEY,
    STORAGE_SERVICE_KEY,
)
from harness.services.storage.sqlite import SQLiteStorageService

logger = structlog.get_logger()


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
        return [STORAGE_SERVICE_KEY, KNOWLEDGE_VAULT_KEY]

    @property
    def trusted(self) -> bool:
        return True

    async def on_load(self, ctx: ServiceContext) -> None:
        db_path = self._db_path or Path.home() / ".harness" / "storage.db"
        if isinstance(db_path, Path):
            db_path.parent.mkdir(parents=True, exist_ok=True)
        self._service = SQLiteStorageService(db_path)
        ctx.provide(STORAGE_SERVICE_KEY, self._service, provider=self.name)
        ctx.provide(KNOWLEDGE_VAULT_KEY, self._service, provider=self.name)
        logger.info("Storage & Knowledge Vault services registered", db_path=str(db_path))

    async def on_unload(self) -> None:
        if self._service:
            self._service.close()
            self._service = None


plugin = StoragePlugin()
