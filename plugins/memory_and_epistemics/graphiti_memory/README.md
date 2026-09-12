# plugin.graphiti_memory (v0.1.0)

Temporal knowledge graph engine with bi-temporal edge invalidation and tri-brid search reranking

---

## Overview & Metadata

- **Plugin Directory**: `plugins/memory_and_epistemics/graphiti_memory`
- **Isolation Mode**: `in_process`
- **Services Provided**: None
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `graphiti_add_episode` | `(content, group_id, source_description)` | Ingest episodic interaction text into the temporal knowledge graph, extracting entities and facts |
| `graphiti_search` | `(query, group_id, limit, include_invalidated)` | Execute tri-brid search (dense vector, BM25 keyword, BFS graph proximity) with balanced merge reranking |
| `graphiti_get_entity` | `(name_or_uuid, group_id)` | Retrieve full entity node state, summaries, attributes, and incident relationships |
| `graphiti_invalidate_fact` | `(edge_uuid, reason)` | Mark a fact relation edge as invalidated with a timestamped record to preserve historical truth |
| `graphiti_get_status` | `(group_id)` | Inspect knowledge graph memory statistics and driver backend health |

---

## Key Modules & AST Symbols

### Module [`engine.py`](engine.py)

Bi-temporal Knowledge Graph Engine with Tri-brid Search & Balanced Merge.

#### Classes

- `class GraphitiMemoryEngine`
  In-memory bi-temporal knowledge graph engine.
  - `def __init__() -> None`
  - `def add_episode(content, group_id, source_description) -> tuple[EpisodicNode, list[EntityNode], list[EntityEdge], int]`
  - `def search(query, group_id, limit, include_invalidated) -> list[tuple[EntityEdge, float]]`
  - `def get_entity(name_or_uuid, group_id) -> EntityNode | None`
  - `def get_entity_relations(entity_uuid, group_id, include_invalidated) -> list[EntityEdge]`
  - `def invalidate_fact(edge_uuid, reason) -> EntityEdge | None`
  - `def get_status(group_id) -> dict[str, Any]`


### Module [`main.py`](main.py)

Graphiti Memory Plugin and HarnessPlugin Service Implementation.

#### Classes

- `class GraphitiMemoryPlugin`
  Harness Plugin implementing GraphitiService and registering GRAPHITI_MEMORY_KEY.
  - `def __init__() -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def add_episode(content, group_id, source_description) -> EpisodeResult`
  - `def search(query, group_id, limit, include_invalidated) -> SearchResult`
  - `def get_entity(name_or_uuid, group_id) -> EntityResult | None`
  - `def invalidate_fact(edge_uuid, reason) -> FactResult | None`
  - `def get_status(group_id) -> GraphitiStatusResult`


#### Functions

- `def graphiti_add_episode(content, group_id, source_description) -> dict[str, Any]`
  - Ingest episodic interaction text into the temporal knowledge graph.
- `def graphiti_search(query, group_id, limit, include_invalidated) -> dict[str, Any]`
  - Execute tri-brid search (dense vector, BM25, BFS) with balanced merge reranking.
- `def graphiti_get_entity(name_or_uuid, group_id) -> dict[str, Any]`
  - Retrieve full entity node state, summaries, attributes, and relationships.
- `def graphiti_invalidate_fact(edge_uuid, reason) -> dict[str, Any]`
  - Mark a fact relation edge as invalidated with a timestamped record.
- `def graphiti_get_status(group_id) -> dict[str, Any]`
  - Inspect knowledge graph memory statistics and driver backend health.


### Module [`models.py`](models.py)

Internal domain models for Graphiti Memory Plugin.

#### Classes

- `class EpisodicNode`
  Represents a raw interaction, turn, document, or temporal event.
- `class EntityNode`
  Represents a resolved semantic concept, agent, or domain object.
- `class EntityEdge`
  Represents a bi-temporal relational fact connecting two entities.



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
