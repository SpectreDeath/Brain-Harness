```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: knowledge-graph-pipeline                                      │
│ SKILL: knowledge-graph-pipeline                                       │
│ Category: data_engineering / meta-skills                             │
│ Version: 1.0.0                                                       │
│ Invocation: /knowledge-graph-pipeline                                │
│ Triggers: "knowledge graph pipeline", "ingest knowledge graph",      │
│           "neo4j pipeline", "recursive sql graph", "gruber modeling" │
│ Requires: "structured-data-scout",                                   │
│           "ontological-engineering-coach",                           │
│           "neo4j-knowledge-graph-architect",                         │
│           "sql-recursive-graph-traversal"                            │
│ Target: End-to-end data scouting, ontological modeling & graph ingest│
└──────────────────────────────────────────────────────────────────────┘
```

# Knowledge Graph Pipeline — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Curated Data Discovery** | Profile tabular schema, cardinality & missingness| Data Quality Profile | Cleaned schema & candidate keys mapped |
| **Stage 2: Ontological Modeling** | Formalize taxonomy meeting Gruber criteria | Ontological Model | 5 Gruber criteria verified with zero bias |
| **Stage 3: Backward LPG Design** | Design graph schema from business queries | LPG Schema Diagram | Constraints, labels & relationships modeled |
| **Stage 4: Idempotent Ingestion** | Ingest via UNWIND batching and MERGE | Batch Ingest Script | 100% records loaded with zero duplication |
| **Stage 5: Dual Traversal** | Execute Cypher and recursive SQL queries | Traversal Benchmark | Shortest path & cycle protection verified |

---

## Vocabulary & Levers

- **Gruber's Ontological Criteria**: Clarity, coherence, extendibility, minimal encoding bias, minimal ontological commitment.
- **Backward LPG Modeling**: Designing graph nodes and relationships working backwards from target query execution patterns.
- **Idempotent MERGE Batching**: Using Cypher `UNWIND $batch AS row MERGE (n ...)` to prevent duplicate nodes across runs.
- **Recursive CTE Cycle Array**: Storing visited node identifiers in an array (`path || node_id`) to halt infinite recursion loops.
- **Null-Safe Property Extraction**: Always using `dict.get(key) or []` to guard against explicit JSON null values (Rule 33).
- **Defensive Batch Exception Logging**: Never using bare `except Exception: continue` in ingestion pipelines (Rule 32).

---

## Mandatory Invariants Checklist

- [ ] **Gruber Ontological Review**: Verify model satisfies all 5 Gruber criteria before database implementation.
- [ ] **Backward-Driven Graph Design**: Design graph schemas starting from target business queries rather than source tables.
- [ ] **Idempotent Ingestion Guarantee**: Always use `MERGE` with uniqueness constraints for batch data insertion.
- [ ] **Recursive SQL Cycle Protection**: Every recursive graph CTE must include explicit cycle detection tracking.
- [ ] **Defensive Batch Exception Logging**: Log unexpected batch processing errors with full diagnostics (Rule 32).
