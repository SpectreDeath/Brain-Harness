# CARD: sql-recursive-graph-traversal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SKILL: sql-recursive-graph-traversal                                        │
│ CATEGORY: Data & Query Engineering                                         │
│ INVOCATION: /sql-recursive-graph-traversal                                  │
│ TRIGGERS: "recursive cte", "sql graph query", "traverse hierarchy sql",   │
│           "cycle detection sql", "shortest path sql", "six degrees sql"     │
│ TARGET: Relational Graph & Hierarchy Querying via WITH RECURSIVE SQL       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5-Stage Progression Matrix

| Stage | Focus Area | Primary Artifact / SQL Construct | Passing Completion Gate |
| :--- | :--- | :--- | :--- |
| **1. Anchor Identification** | Root Seeding & State Init | `SELECT ... AS hop_count, path_string, cost` | Anchor query isolates seed roots with zero state pollution. |
| **2. Recursive Expansion** | Edge Traversal & Metric Accumulation | `JOIN ... ON t.destination = e.origin` | Working set joins iteratively, accumulating cost and path history. |
| **3. Cycle Defense** | Loop Prevention & Depth Brakes | `WHERE instr(path, next) = 0 AND hop_count < N` | Cyclic branches pruned; hard recursion ceiling actively enforced. |
| **4. Target Windowing** | BFS Shortest Path Selection | `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` | Target matches ranked; minimum-hop/cheapest route extracted. |
| **5. Index Tuning** | Query Execution Plan Profiling | `CREATE INDEX idx_edges_origin` + `EXPLAIN` | Foreign key joins indexed; table scan costs eliminated. |

---

## The Three Core Pillars

```
┌─────────────────────────────────────────────────────────────┐
│ 1. THE RECURSIVE ANCHOR SEED                                │
│ - Seeds the working table with initial hop 0 or root nodes. │
│ - Initializes tracker columns: hop_count, path, total_cost. │
├─────────────────────────────────────────────────────────────┤
│ 2. THE DUAL-LAYER CYCLE DEFENSE                             │
│ - Layer 1: Visited Path Membership check (prunes loops).    │
│ - Layer 2: Hard Depth Brake (WHERE hop_count < 20).         │
├─────────────────────────────────────────────────────────────┤
│ 3. THE BFS SHORTEST-PATH WINDOW                             │
│ - Partitions results by destination node.                   │
│ - Extracts rn = 1 for deterministic minimum-hop paths.      │
└─────────────────────────────────────────────────────────────┘
```

---

## Anti-Pattern Invariants Checklist

- [ ] **Acyclic / Cycle Guard**: Every recursive CTE over non-tree graphs contains a visited path check.
- [ ] **Hard Depth Ceiling**: Query includes `hop_count < N` safety bound to prevent infinite recursion.
- [ ] **Delimited Path Formatting**: Node IDs are tracked with delimiters (e.g. `/10/ -> /20/`) to prevent substring collisions.
- [ ] **Join Column Indexing**: Foreign keys in recursive join conditions are backed by database indexes.
- [ ] **Working Table Size Guard**: Recursive scans are constrained on wide, dense graphs to avoid disk spills.
