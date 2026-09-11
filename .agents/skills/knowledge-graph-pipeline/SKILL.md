---
name: knowledge-graph-pipeline
description: Ingest curated tabular datasets into governed Neo4j labeled property graphs and relational recursive SQL hierarchies using ontological engineering standards. Do not use for ad-hoc unstructured document search or raw key-value caches.
---

# Knowledge Graph Pipeline: Curated Data to Governed Graph Traversal

`knowledge-graph-pipeline` is an authoritative composite meta-skill that orchestrates the discovery, ontological modeling, ingestion, and dual-engine querying of interconnected structured datasets into enterprise graph architectures.

It coordinates four specialized capabilities:
1. **Curated Structured Data Discovery** ([`structured-data-scout`](../structured-data-scout/SKILL.md))
2. **Ontological Engineering & Formal Modeling** ([`ontological-engineering-coach`](../ontological-engineering-coach/SKILL.md))
3. **Neo4j Labeled Property Graph Architecture** ([`neo4j-knowledge-graph-architect`](../neo4j-knowledge-graph-architect/SKILL.md))
4. **Relational Recursive SQL Graph Traversal** ([`sql-recursive-graph-traversal`](../sql-recursive-graph-traversal/SKILL.md))

See [CARD.md](CARD.md) for the companion summary card, 5-stage progression matrix, and invariants checklist.
Consult `/ontological-engineering-coach` for Gruber criteria, `/neo4j-knowledge-graph-architect` for Cypher UNWIND batching, and [graph-patterns.md](references/graph-patterns.md) for graph design patterns.

---

## The 5-Stage Knowledge Graph Progression

```
[1. Curated Data Discovery] ──► [2. Ontological Modeling] ──► [3. Backward LPG Design]
                                                                        │
                                                                        ▼
[5. Dual-Engine Traversal] ◄── [4. Idempotent Batch Ingestion] ◄────────┘
```

---

## 1. Curated Data Discovery & Scouting

Source, clean, and validate tabular datasets from reputable repositories before graph modeling:

1. **Dataset Identification & Acquisition**:
   - Query curated repositories (UCI Machine Learning, Kaggle, OpenData, HuggingFace Datasets) without unstructured web scraping.
2. **Schema & Null-Field Profiling (Rule 33)**:
   - Profile data types, foreign key integrity, missingness, and cardinality distributions.
   - Enforce explicit null-value fallback handling (`dict.get(key) or []`).
3. **Data Quality Gating**:
   - Verify accuracy, completeness, consistency, timeliness, validity, and uniqueness.

> **Completion criterion**: Cleaned dataset schema profiled with entity candidate keys and cardinality ratios documented.

---

## 2. Ontological Engineering & Gruber Modeling

Formalize concepts, taxonomic hierarchies, and semantic relationships using formal engineering principles:

1. **Apply Gruber's 5 Ontological Criteria**:
   - **Clarity**: Unambiguous definitions independent of computational context.
   - **Coherence**: Logical consistency with zero contradictory inferences.
   - **Extendibility**: Monotonic expansion without revising existing axioms.
   - **Minimal Encoding Bias**: Conceptual modeling free of database-specific representation quirks.
   - **Minimal Ontological Commitment**: Constraining only what is strictly necessary.
2. **Taxonomy & Axiom Definition**:
   - Formalize `is-a` taxonomies, `part-of` mereologies, and domain/range constraints.

> **Completion criterion**: Ontological schema formalized meeting all five Gruber design criteria.

---

## 3. Backward LPG Schema Design

Design the Neo4j Labeled Property Graph (LPG) schema working backward from downstream query patterns:

1. **Query-Driven Schema Modeling**:
   - Derive node labels, relationship types, and directional arrows from essential business questions.
2. **Node vs Property Allocation**:
   - Model entities with distinct lifecycles as Nodes; model scalar attributes as Properties.
3. **Constraint & Index Declarations**:
   - Define uniqueness constraints (`IS UNIQUE`) and existence constraints (`IS NOT NULL`) to guarantee data integrity.

> **Completion criterion**: Backward-designed LPG schema with uniqueness constraints and traversal paths documented.

---

## 4. Idempotent Batch Ingestion

Ingest large tabular payloads into Neo4j using memory-efficient transactional batching:

1. **Cypher UNWIND Batching**:
   - Structure ingestion queries using `UNWIND $batch AS row` to bound transaction memory.
2. **Idempotent MERGE Semantics**:
   - Use `MERGE (n:Entity {id: row.id}) ON CREATE SET ... ON MATCH SET ...` to guarantee safe re-execution.
3. **Transaction Slicing & Error Visibility (Rule 32)**:
   - Chunk large datasets into 1,000 to 5,000 item slices; log all batch exceptions loudly without silent swallowing.

> **Completion criterion**: Idempotent batch ingestion script executed with 100% records loaded and zero duplicate nodes.

---

## 5. Dual-Engine Traversal & Recursive SQL

Execute complex graph pathfinding across both dedicated graph databases and relational SQL engines:

1. **Neo4j Native Path Traversal**:
   - Execute variable-length relationship expansions (`()-[:DEPENDS_ON*1..5]->()`) and shortest-path algorithms.
2. **Relational Recursive Common Table Expressions (CTEs)**:
   - Execute BFS shortest-path, hierarchy walking, and cycle detection inside relational SQL engines without graph infrastructure.
3. **Cycle Safety Invariant**:
   - Include cycle-prevention arrays (`ARRAY[id]` or string path trackers) in all recursive CTE queries to prevent infinite loops.

> **Completion criterion**: Traversal queries successfully executed across both Cypher and Recursive SQL with cycle protection.

---

## The Three Foundational Pillars

### 1. The Visual Brief Pillar
Every knowledge graph cycle renders an interactive HTML visual brief in `%TEMP%` displaying the ontological entity hierarchy, LPG schema diagrams, and traversal query benchmarks.

### 2. The Mandatory Checkpoint Pillar
The agent must never execute destructive schema migrations or large batch drops without first presenting `implementation_plan.md` with `RequestFeedback: true` and awaiting explicit user confirmation.

### 3. Explicit Anti-Patterns
Rigid architectural boundaries prevent schema bloat, unbounded recursive loops, and silent ingestion failures.

---

## Anti-Patterns

- **Forward Schema Guessing** — Designing complex graph schemas speculatively before identifying downstream traversal queries.
- **Unbounded Recursive CTE Loops** — Writing recursive SQL hierarchy queries without explicit depth bounds or cycle detection arrays.
- **Non-Idempotent Ingestion** — Using bare `CREATE` statements in batch ingestion instead of `MERGE` with uniqueness constraints.
- **Bare Catch Ingestion Swallowing** — Catching batch ingestion exceptions with bare `except Exception: continue` without logging (Rule 32).
- **Property Bloating Entities** — Flattening interconnected domain entities into massive string properties on a single node.
- **Missing Negative Boundaries** — Scaffolding graph skills without explicit `Do not use for...` constraints in frontmatter descriptions.
