"""Single-seam service resolvers for storage and knowledge vault per Rule 58."""

from __future__ import annotations

from pathlib import Path

from harness.kernel.context import ServiceContext
from harness.services.storage.protocols import (
    KNOWLEDGE_VAULT_KEY,
    STORAGE_SERVICE_KEY,
    StorageService,
)
from harness.services.storage.sqlite import SQLiteStorageService


def resolve_storage_service(
    context: ServiceContext | None = None,
    db_path: Path | str = ":memory:",
) -> StorageService:
    """Resolve StorageService from IoC container if available, else instantiate default."""
    if context and context.has(STORAGE_SERVICE_KEY):
        return context.require(STORAGE_SERVICE_KEY)
    return SQLiteStorageService(db_path)


def resolve_knowledge_vault(
    context: ServiceContext | None = None,
    db_path: Path | str = ":memory:",
) -> StorageService:
    """Resolve Knowledge Vault StorageService from IoC container if available, else instantiate default."""
    if context and context.has(KNOWLEDGE_VAULT_KEY):
        return context.require(KNOWLEDGE_VAULT_KEY)
    if context and context.has(STORAGE_SERVICE_KEY):
        return context.require(STORAGE_SERVICE_KEY)
    return SQLiteStorageService(db_path)
