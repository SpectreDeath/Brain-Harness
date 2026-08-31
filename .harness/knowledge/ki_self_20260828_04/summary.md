# Knowledge Item: Relational Recursive CTE Graph Cycle Brakes

- **ID**: `ki_self_20260828_04`
- **Category**: `data_engineering` / `sql`
- **Status**: `VERIFIED`

## Summary & Heuristic

Relational SQL databases (SQLite, PostgreSQL, MySQL) can execute graph algorithms (BFS, shortest path, hierarchy resolution) using recursive CTEs without external graph stores, provided cycles are safely pruned.

### Core Guidelines:
1. **Anchor & Recursive Member**:
   - Seed the CTE with origin nodes (`hop_count = 0`, `path = '/' || id || '/'`, `total_cost = 0`).
   - Recursively join edge tables on `edge.source_id = cte.current_id`.
2. **Cycle Prevention via Path Substring Matching**:
   - In SQLite/Postgres, append visited nodes to a delimited string (`path || edge.target_id || '/'`).
   - Check `INSTR(cte.path, '/' || edge.target_id || '/') = 0` (or `NOT (edge.target_id = ANY(cte.visited_array))` in Postgres).
3. **Hard Depth Bounding**:
   - Always include `WHERE cte.hop_count < :max_hops` as a safety brake.
4. **BFS Shortest Path Windowing**:
   - Partition final results by target node and order by `hop_count` / `total_cost` using `ROW_NUMBER() OVER (PARTITION BY target_id ORDER BY hop_count ASC) = 1`.
