"""Storage service package — key-value and document storage interface.

Provides persistent storage that other plugins can use for state,
configuration, and data. Ships with a SQLite-backed implementation.
"""

from __future__ import annotations

from harness.services.storage.isnad import IsnadAuditMixin
from harness.services.storage.models import (
    IsnadClaim,
    IsnadClaimStatus,
    IsnadLineageBlock,
    IsnadLineageNode,
    KnowledgeEdge,
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
from harness.services.storage.vault_contradiction import (
    ContradictionDetector,
    ContradictionReviewItem,
)
from harness.services.storage.vault_graph import KnowledgeGraphQueryService
from harness.services.storage.vault_operations import KnowledgeVaultMixin
from harness.services.storage.vault_retrieval import KnowledgeRetrievalMixin
from harness.services.storage.vault_taxonomy import (
    TaxonomyDomain,
    get_taxonomy_domain,
    normalize_category,
)

__all__ = [
    "KNOWLEDGE_VAULT_KEY",
    "STORAGE_SERVICE_KEY",
    "ContradictionDetector",
    "ContradictionReviewItem",
    "IsnadAuditMixin",
    "IsnadClaim",
    "IsnadClaimStatus",
    "IsnadLineageBlock",
    "IsnadLineageNode",
    "KnowledgeEdge",
    "KnowledgeGraphQueryService",
    "KnowledgeItemRecord",
    "KnowledgeRetrievalMixin",
    "KnowledgeVaultMixin",
    "SQLiteStorageService",
    "StoragePlugin",
    "StorageService",
    "TaxonomyDomain",
    "get_taxonomy_domain",
    "normalize_category",
    "plugin",
    "resolve_knowledge_vault",
    "resolve_storage_service",
]
