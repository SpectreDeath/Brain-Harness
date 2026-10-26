"""Storage service package — key-value and document storage interface.

Provides persistent storage that other plugins can use for state,
configuration, and data. Ships with a SQLite-backed implementation.
"""

from __future__ import annotations

from harness.services.storage.isnad import IsnadAuditMixin
from harness.services.storage.models import (
    IsnadLineageBlock,
    IsnadLineageNode,
    KnowledgeItemRecord,
)
from harness.services.storage.plugin import StoragePlugin, plugin
from harness.services.storage.protocols import (
    KNOWLEDGE_VAULT_KEY,
    STORAGE_SERVICE_KEY,
    StorageService,
)
from harness.services.storage.resolvers import (
    resolve_knowledge_vault,
    resolve_storage_service,
)
from harness.services.storage.sqlite import SQLiteStorageService
from harness.services.storage.vault_operations import KnowledgeVaultMixin
from harness.services.storage.vault_retrieval import KnowledgeRetrievalMixin

__all__ = [
    "KNOWLEDGE_VAULT_KEY",
    "STORAGE_SERVICE_KEY",
    "IsnadAuditMixin",
    "IsnadLineageBlock",
    "IsnadLineageNode",
    "KnowledgeItemRecord",
    "KnowledgeRetrievalMixin",
    "KnowledgeVaultMixin",
    "SQLiteStorageService",
    "StoragePlugin",
    "StorageService",
    "plugin",
    "resolve_knowledge_vault",
    "resolve_storage_service",
]
