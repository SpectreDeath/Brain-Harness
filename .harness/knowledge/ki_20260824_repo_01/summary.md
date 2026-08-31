# KI-1: Bi-Temporal Edge Invalidation in Dynamic Knowledge Graphs

## Overview & Architectural Motivation
Traditional knowledge graphs and vector databases treat entity updates either as destructive overwrites (losing past truth) or duplicate insertions (creating contradictory retrieval noise). In Graphiti, knowledge is structured bi-temporally across two distinct temporal axes:
1. **Transaction Time (`created_at`)**: When the fact was recorded in the database.
2. **Valid Time (`valid_at` / `invalid_at` / `expired_at`)**: The real-world temporal validity interval of the fact.

## Implementation Pattern in `graphiti_core`

From `graphiti_core/edges.py`:
```python
class EntityEdge(Edge):
    """Represents a directional relationship between two entities."""
    source_node_uuid: str
    target_node_uuid: str
    name: str
    fact: str
    episodes: list[str] = Field(default_factory=list)
    valid_at: datetime | None = None
    invalid_at: datetime | None = None
    expired_at: datetime | None = None
```

### Invalidation Mechanics
When new episode content contradicts an existing fact (e.g., "Alice lives in Berlin" &rarr; "Alice moved to Tokyo"):
1. The LLM extraction and deduplication pass identifies that the relation `(Alice)-[LIVES_IN]->(Berlin)` has been superseded.
2. Rather than executing a `DELETE` query, the engine runs an update setting:
   ```cypher
   MATCH (s:Entity {uuid: $source_uuid})-[r:RELATES_TO {uuid: $edge_uuid}]->(t:Entity {uuid: $target_uuid})
   SET r.invalid_at = $current_episode_timestamp
   ```
3. A new edge `(Alice)-[LIVES_IN]->(Tokyo)` is created with `valid_at = $current_episode_timestamp` and `invalid_at = NULL`.
4. Active fact retrieval filters for current truth:
   ```cypher
   WHERE r.invalid_at IS NULL OR r.invalid_at > $query_time
   ```

## Application to Brain Harness
- Use this pattern in Brain Harness memory plugins (`plugin.memory_*` or context graphs) to record evolving codebase decisions, user preferences, and agent task states without loss of historical traceability.
