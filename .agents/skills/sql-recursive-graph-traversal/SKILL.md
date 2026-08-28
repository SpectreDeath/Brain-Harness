---
name: sql-recursive-graph-traversal
description: Execute graph pathfinding, hierarchy walking, cycle detection, path cost accumulation, and BFS shortest-path queries inside relational SQL without dedicated graph database infrastructure. Trigger when querying hierarchical trees, organizational charts, bill-of-materials, route planning, cycle-safe network graphs, or computing degrees of separation.
---

# SQL Recursive Graph Traversal Engine

`sql-recursive-graph-traversal` operationalizes relational SQL as a declarative graph query engine via Recursive Common Table Expressions (`WITH RECURSIVE`). It solves graph traversal, hierarchy walking, pathfinding, cost accumulation, and shortest-path breadth-first searches directly inside relational database engines (PostgreSQL, SQLite, MySQL 8+, SQL Server) without requiring external graph database dependencies or procedural scripts.

Every graph traversal workflow executes this five-stage progression:

```
[1. Topology & Anchor Identification] → [2. Recursive Expansion & State Tracking] → [3. Cycle Defense & Safety Brakes] → [4. Target Filtering & Shortest-Path Windowing] → [5. Index & Performance Tuning]
```

See [CARD.md](CARD.md) for the companion summary card, SQL recursion template library, and verification invariants.
Consult `/data-topology-mapper` for structural blast radius mapping and `/epistemic-isnad-audit` for dependency lineage.

---

## 1. Topology & Anchor Identification

Define the graph representation in relational tables and formulate the anchor member:

1. **Classify the Edge Schema**:
   - **Direct Adjacency List**: `(id, parent_id, label)` — standard tree/hierarchy.
   - **Directed Edge List**: `(origin, destination, cost, distance)` — weighted route graph.
   - **Undirected / Bidirectional Network**: `(node_a, node_b)` — social graph (requires symmetric union in anchor or recursive step).
2. **Formulate the Anchor Query**:
   - Seed the initial working set (root nodes, start locations, or source individuals).
   - Initialize state tracking columns:
     - `depth` or `level` (initialized to `0` or `1`).
     - `path_string` (initialized to `CAST(node_id AS TEXT)` or `origin || ' -> ' || destination`).
     - `accumulated_cost` (initialized to `0.0` or direct edge cost).
     - `is_cycle` (initialized to `0` or `FALSE`).

```sql
WITH RECURSIVE graph_traversal AS (
    -- 1. Anchor Member: Seed the root / origin
    SELECT 
        origin,
        destination,
        cost,
        1 AS hop_count,
        cost AS total_cost,
        origin || ' -> ' || destination AS path_string,
        0 AS is_cycle
    FROM flights
    WHERE origin = 'JFK'
    
    UNION ALL
    
    -- 2. Recursive Member (Structured in Stage 2 & 3)
    ...
)
```

> **Completion criterion**: Anchor query defined, seeding initial working nodes with explicit `hop_count`, `total_cost`, `path_string`, and `is_cycle` tracker columns.

---

## 2. Recursive Expansion & State Tracking

Construct the recursive member to expand neighbor nodes while accumulating path metrics:

1. **Join Condition**:
   - Join the recursive working set `t` with the base edge table `e` where `t.destination = e.origin` (or `t.child_id = e.parent_id`).
2. **Metric Accumulation**:
   - Increment hop count: `t.hop_count + 1`.
   - Add running costs: `t.total_cost + e.cost`.
   - Concatenate path history: `t.path_string || ' -> ' || e.destination`.
3. **State Isolation**:
   - Ensure all derived columns maintain exact data type alignment across the `UNION ALL` boundary.

> **Completion criterion**: Recursive member joins working set to edge table, propagating accumulated metrics and path history across iterative hops.

---

## 3. Cycle Defense & Safety Brakes

Prevent infinite recursion loops and memory exhaustion on cyclic or bidirectional graphs:

```
┌─────────────────────────────────────────────────────────────┐
│               CYCLE DEFENSE IN RECURSIVE SQL                │
├──────────────────────────────┬──────────────────────────────┤
│ Mechanism 1: Visited Path    │ Mechanism 2: Hard Depth Brake│
│ - String: instr(path, next)  │ - WHERE hop_count < 20       │
│ - Array: next = ANY(path)    │ - Guards unexpected loops    │
└──────────────────────────────┴──────────────────────────────┘
```

1. **Visited Path Membership Check**:
   - **SQLite / Text Engines**: Use `instr(t.path_string, e.destination) > 0` or delimited search `instr('/' || t.path_string || '/', '/' || e.destination || '/') > 0`.
   - **PostgreSQL**: Use array accumulator `e.destination = ANY(t.visited_nodes)`.
2. **Prune Cyclic Branches**:
   - Add filter in the recursive `WHERE` clause: `WHERE instr(t.path_string, e.destination) = 0` (or set `is_cycle = 1` and halt expansion).
3. **Inject Hard Depth Brake**:
   - Enforce a hard recursion boundary: `AND t.hop_count < :max_depth` (e.g., `< 20`). This acts as a circuit breaker against unexpected dense cycles.

```sql
    UNION ALL
    
    SELECT 
        e.origin,
        e.destination,
        e.cost,
        t.hop_count + 1,
        t.total_cost + e.cost,
        t.path_string || ' -> ' || e.destination,
        CASE WHEN instr(t.path_string, e.destination) > 0 THEN 1 ELSE 0 END
    FROM flights e
    JOIN graph_traversal t ON t.destination = e.origin
    WHERE instr(t.path_string, e.destination) = 0  -- Cycle Defense
      AND t.hop_count < 10                         -- Hard Depth Brake
```

> **Completion criterion**: Cycle detection condition and hard depth ceiling embedded into the recursive `WHERE` clause, eliminating infinite loop paths.

---

## 4. Target Filtering & Shortest-Path Windowing

Filter the completed working set for destination criteria and calculate shortest or cheapest paths:

1. **Terminal Destination Filter**:
   - In the outer `SELECT`, filter for target vertices: `WHERE destination = 'NRT'`.
2. **Breadth-First Shortest Path (BFS Windowing)**:
   - When multiple paths reach the same destination at different depths, rank them using window functions:
     ```sql
     WITH ranked_paths AS (
         SELECT 
             destination,
             path_string,
             hop_count,
             total_cost,
             ROW_NUMBER() OVER (
                 PARTITION BY destination 
                 ORDER BY hop_count ASC, total_cost ASC
             ) AS rank_order
         FROM graph_traversal
         WHERE destination = 'NRT'
     )
     SELECT * FROM ranked_paths WHERE rank_order = 1;
     ```
3. **Format Output Hierarchies**:
   - For organizational trees, render formatted visual indentation using `substr('          ', 1, level * 2) || employee_name`.

> **Completion criterion**: Outer query filters target destination, ranks paths via window partition, and returns deterministic shortest or lowest-cost trajectories.

---

## 5. Index & Performance Tuning

Profile query execution plans and protect database memory bounds:

1. **Index Recursive Join Columns**:
   - Ensure an index exists on the foreign key / join column: `CREATE INDEX idx_edges_origin ON flights(origin, destination, cost);`
   - *Failure to index results in a full table scan on every recursive iteration.*
2. **Bound Working Table Size**:
   - For highly connected, dense networks (e.g., social networks with thousands of edges per node), avoid unconstrained multi-hop scans that spill intermediate tables to disk.
3. **Validate Execution Plan**:
   - Run `EXPLAIN QUERY PLAN` (SQLite) or `EXPLAIN ANALYZE` (PostgreSQL) to verify index usage and scan costs.

> **Completion criterion**: Join indexes verified, working table memory bounds checked, and query execution plan validated.

---

## In-File Reference: SQL Recursion Patterns

### Pattern A: Org Chart Tree Traversal (Hierarchy & Indentation)
```sql
WITH RECURSIVE org_tree AS (
    SELECT id, name, manager_id, 0 AS level, name AS path
    FROM employees WHERE manager_id IS NULL
    UNION ALL
    SELECT e.id, e.name, e.manager_id, t.level + 1, t.path || ' -> ' || e.name
    FROM employees e
    JOIN org_tree t ON e.manager_id = t.id
    WHERE t.level < 15
)
SELECT printf('%*s', level * 2, '') || name AS indented_tree, level, path
FROM org_tree ORDER BY path;
```

### Pattern B: Shortest Path Breadth-First-Search (Six Degrees)
```sql
WITH RECURSIVE network_paths AS (
    SELECT person_b AS current_node, 1 AS degree, person_a || ' -> ' || person_b AS path
    FROM friendships WHERE person_a = 'Alice'
    UNION ALL
    SELECT f.person_b, p.degree + 1, p.path || ' -> ' || f.person_b
    FROM friendships f
    JOIN network_paths p ON f.person_a = p.current_node
    WHERE instr(p.path, f.person_b) = 0 AND p.degree < 6
),
shortest AS (
    SELECT current_node, degree, path,
           ROW_NUMBER() OVER (PARTITION BY current_node ORDER BY degree ASC) AS rn
    FROM network_paths
)
SELECT current_node AS target_person, degree, path
FROM shortest WHERE rn = 1;
```

---

## Anti-Patterns

- **Unbounded Recursive Queries** — Omitting depth brakes and cycle checks, allowing circular graphs to loop until out-of-memory crashes occur.
- **Unindexed Recursive Joins** — Joining recursive working sets to unindexed base tables, turning every recursion step into an $O(N)$ full table scan.
- **Dense Graph Fan-Out Explosion** — Running deep recursive CTEs across highly connected social networks where intermediate working tables explode exponentially.
- **Missing Path String Delimiters** — Using substring checks without delimiters (e.g. searching for `1` inside `10 -> 21`), causing false-positive cycle triggers. Use delimited formats like `/1/ -> /10/`.
