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
from harness.services.storage.vault_backfill import (
    backfill_edges_mechanically,
    propose_links,
)
from harness.services.storage.vault_contradiction import (
    ContradictionDetector,
    ContradictionReviewItem,
)
from harness.services.storage.vault_derivation import derive_knowledge_graph
from harness.services.storage.vault_exporters import (
    export_gexf,
    export_graphml,
    export_html,
    export_json,
    export_knowledge_graph,
)
from harness.services.storage.vault_graph import (
    KNOWLEDGE_GRAPH_SERVICE_KEY,
    KnowledgeGraphQueryService,
    resolve_knowledge_graph_service,
    validate_export_path,
)
from harness.services.storage.vault_graph_models import (
    DerivedKnowledgeGraph,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    KnowledgeGraphSummary,
)
from harness.services.storage.vault_html_exporter import export_html
from harness.services.storage.vault_hygiene import (
    audit_vault_hygiene,
    suggest_category_for_item,
    suggest_tags_for_item,
)
from harness.services.storage.vault_operations import KnowledgeVaultMixin
from harness.services.storage.vault_retrieval import KnowledgeRetrievalMixin
from harness.services.storage.vault_taxonomy import (
    TaxonomyDomain,
    get_taxonomy_domain,
    normalize_category,
    normalize_isnad,
    resolve_created_at,
    resolve_source_target,
)
from harness.services.storage.vault_traversal import (
    bfs_shortest_path,
    find_node_neighbors,
    find_vault_orphans,
)

__all__ = [
    "DerivedKnowledgeGraph",
    "KNOWLEDGE_GRAPH_SERVICE_KEY",
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
    "KnowledgeGraphEdge",
    "KnowledgeGraphNode",
    "KnowledgeGraphQueryService",
    "KnowledgeGraphSummary",
    "KnowledgeItemRecord",
    "KnowledgeRetrievalMixin",
    "KnowledgeVaultMixin",
    "SQLiteStorageService",
    "StoragePlugin",
    "StorageService",
    "TaxonomyDomain",
    "audit_vault_hygiene",
    "backfill_edges_mechanically",
    "bfs_shortest_path",
    "derive_knowledge_graph",
    "export_gexf",
    "export_graphml",
    "export_html",
    "export_json",
    "export_knowledge_graph",
    "find_node_neighbors",
    "find_vault_orphans",
    "get_taxonomy_domain",
    "normalize_category",
    "normalize_isnad",
    "plugin",
    "propose_links",
    "resolve_created_at",
    "resolve_knowledge_graph_service",
    "resolve_knowledge_vault",
    "resolve_source_target",
    "resolve_storage_service",
    "suggest_category_for_item",
    "suggest_tags_for_item",
    "validate_export_path",
]
