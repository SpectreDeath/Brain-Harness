# Storage & Knowledge Vault Service

The `harness.services.storage` subpackage provides enterprise storage abstractions, SQLite-backed persistence, cryptographic Isnad chain-of-custody audit ledgers, and bidirectional Knowledge Vault graph operations.

---

## Architectural Invariants

- **Typed IoC Resolution (`Rule 2`)**: The storage service is registered under `STORAGE_SERVICE_KEY` (`ServiceKey[StorageService]`) and resolved via `context.require(STORAGE_SERVICE_KEY)` or `resolve_storage_service(context)`.
- **Append-Only & Isnad Provenance (`Rule 4`, `Rule 22`)**: All facts and epistemic items maintain immutable chain-of-custody ledgers (`IsnadAuditMixin`, `IsnadClaim`).
- **Slotted & Frozen Dataclasses (`Rule 12`)**: High-volume graph models (`KnowledgeGraphNode`, `KnowledgeGraphEdge`, `KnowledgeGraphSummary`) declare `slots=True` and `frozen=True`.
- **Multi-Store Autobiographical Memory Federation (`Rule 22`)**: Read queries against active SQLite stores use URI mode `mode=ro` to eliminate lock contention with concurrent proactors.

---

## Module & Symbol Reference

| Module | Core Classes / Symbols | Description |
|---|---|---|
| [`protocols.py`](protocols.py) | `StorageService`, `STORAGE_SERVICE_KEY` | Abstract protocol defining key-value, document, and transactional storage contracts. |
| [`sqlite.py`](sqlite.py) | `SQLiteStorageService` | High-performance SQLite storage implementation with ACID transactions and JSON extraction. |
| [`models.py`](models.py) | `IsnadClaim`, `IsnadClaimStatus`, `KnowledgeEdge` | Epistemic provenance models and directional relationship records. |
| [`resolvers.py`](resolvers.py) | `resolve_storage_service`, `resolve_knowledge_vault` | Single-seam IoC resolution helpers for storage and knowledge vault instances. |
| [`isnad.py`](isnad.py) | `IsnadAuditMixin` | Cryptographic SHA-256 hash chaining and lineage verification mixin. |
| [`vault_operations.py`](vault_operations.py) | `KnowledgeVaultMixin` | Dual-file directory CRUD operations conforming to `Rule 40`. |
| [`vault_graph.py`](vault_graph.py) | `KnowledgeGraphQueryService` | Topological pathfinding, orphan detection, and edge traversal service. |
| [`vault_graph_models.py`](vault_graph_models.py) | `KnowledgeGraphNode`, `KnowledgeGraphEdge` | Slotted graph entity and relationship representations. |
| [`vault_traversal.py`](vault_traversal.py) | `bfs_shortest_path`, `find_node_neighbors`, `find_vault_orphans` | In-memory graph traversal algorithms. |
| [`vault_sqlite_graph.py`](vault_sqlite_graph.py) | `init_ki_edges_table`, `sync_ki_edges`, `find_path_sql` | Relational SQLite recursive CTE graph queries per `sql-recursive-graph-traversal`. |
| [`vault_exporters.py`](vault_exporters.py) | `export_json`, `export_gexf`, `export_graphml` | Multi-format graph serialization engine. |
| [`vault_cypher_exporter.py`](vault_cypher_exporter.py) | `export_cypher` | Idempotent Cypher statement batch exporter for Neo4j property graphs. |
| [`vault_contradiction.py`](vault_contradiction.py) | `ContradictionDetector`, `ContradictionReviewItem` | Antinomy and claim conflict detection engine. |
| [`vault_hygiene.py`](vault_hygiene.py) | `audit_vault_hygiene`, `suggest_category_for_item` | Automated vault validation and category normalization. |
| [`vault_taxonomy.py`](vault_taxonomy.py) | `TaxonomyDomain`, `normalize_category` | Controlled hierarchical taxonomy domain classification. |
| [`vault_html_exporter.py`](vault_html_exporter.py) | `render_html`, `build_domain_mermaid` | Interactive standalone dark-mode HTML visual brief rendering. |

---

## Usage Recipes

### Resolving and Storing Structured Documents
```python
from harness.kernel.context import ServiceContext
from harness.services.storage import resolve_storage_service

def record_session_artifact(context: ServiceContext, session_id: str, data: dict) -> None:
    storage = resolve_storage_service(context)
    storage.set_json(f"sessions/{session_id}", data)
```

### Querying Knowledge Graph Lineage
```python
from harness.services.storage.vault_traversal import bfs_shortest_path
from harness.services.storage.vault_graph import KnowledgeGraphQueryService

def trace_concept_lineage(service: KnowledgeGraphQueryService, source_id: str, target_id: str):
    path = bfs_shortest_path(service.graph, source_id, target_id)
    return path
```

