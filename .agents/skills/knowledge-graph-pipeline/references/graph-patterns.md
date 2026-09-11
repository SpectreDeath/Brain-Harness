# Knowledge Graph Modeling & Traversal Patterns

## 1. Idempotent Cypher Ingestion Pattern
Always load tabular records using parameter batching with `UNWIND`:

```cypher
UNWIND $batch AS row
MERGE (source:Entity {id: row.source_id})
  ON CREATE SET source.name = row.source_name, source.created_at = datetime()
MERGE (target:Concept {id: row.target_id})
  ON CREATE SET target.title = row.target_title
MERGE (source)-[r:RELATES_TO]->(target)
  ON CREATE SET r.weight = toFloat(row.weight)
```

## 2. Relational Recursive SQL Hierarchy Pattern with Cycle Safety
Query hierarchical graphs in relational SQL engines without infinite loops:

```sql
WITH RECURSIVE graph_walk AS (
    -- Anchor member
    SELECT 
        node_id, 
        parent_id, 
        1 AS depth, 
        ARRAY[node_id] AS path,
        FALSE AS is_cycle
    FROM hierarchy_edges
    WHERE parent_id IS NULL

    UNION ALL

    -- Recursive member
    SELECT 
        e.node_id, 
        e.parent_id, 
        gw.depth + 1, 
        gw.path || e.node_id,
        e.node_id = ANY(gw.path)
    FROM hierarchy_edges e
    JOIN graph_walk gw ON e.parent_id = gw.node_id
    WHERE NOT gw.is_cycle AND gw.depth < 10
)
SELECT * FROM graph_walk WHERE NOT is_cycle;
```
