# CARD: neo4j-knowledge-graph-architect

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SKILL: neo4j-knowledge-graph-architect                                      │
│ Domain: Data Engineering                                                    │
│ Version: 1.0.0                                                              │
│ Invocation: /neo4j-knowledge-graph-architect                                 │
│ Triggers: "neo4j graph", "cypher query", "knowledge graph schema",          │
│           "property graph", "graph ingestion", "epistemic graph"            │
│ Target: Production Neo4j LPG architecture, backward schema modeling,         │
│         idempotent batch ingestion, traversal safety, index profiling       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5-Stage Progression Matrix

| Stage | Focus Area | Primary Artifact / Cypher Pattern | Passing Completion Gate |
| :--- | :--- | :--- | :--- |
| **1. Schema Design** | Semantic Modeling & Partitions | `(:Entity)-[:TYPED_REL {props}]->(:Target)` | Schema models backwards from questions with temporal evidence properties. |
| **2. Batch Ingestion** | Constraints & Idempotent UNWIND | `CREATE CONSTRAINT` + `UNWIND $batch MERGE` | Uniqueness constraints active; parameterized UNWIND batches run idempotently. |
| **3. Query Engineering** | Traversal Bounds & Trail Safety | `MATCH ... WITH ... MATCH` + `[*1..4]` | Explicit upper bounds enforced; diamond traversals split across WITH clauses. |
| **4. Index Profiling** | Execution Plan & dbHits Tuning | `EXPLAIN` & `PROFILE` analysis | NodeIndexSeek verified on anchor roots; CartesianProduct eliminated. |
| **5. Test Harnessing** | Ephemeral Integration Assertions | Real Neo4j container + DETACH DELETE | Double-load test yields identical counts; constraint errors handled gracefully. |

---

## The Three Core Pillars

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. SCHEMA BACKWARDS FROM QUESTIONS                                          │
│ - Derive nodes, edges, and properties directly from target competency       │
│   questions. Entities with independent lifecycles become nodes; scalar      │
│   attributes become properties; directed connections become explicit edges. │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. IDENTITY-ISOLATED MERGE                                                  │
│ - Scope MERGE to a single immutable natural identity property. Set mutable  │
│   attributes exclusively inside ON CREATE SET and ON MATCH SET clauses to    │
│   eliminate duplicate node explosion.                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. TRAIL-SAFE WITH-SPLIT TRAVERSAL                                          │
│ - Overcome Cypher relationship uniqueness trail semantics by splitting      │
│   diamond patterns and cyclic traversals across separate MATCH and WITH     │
│   stages, preventing silent row drops on multi-path traversals.             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Disambiguation Routing Table

| Requirement / Architecture | Technology | Dispatched Skill |
| :--- | :--- | :--- |
| Labeled Property Graph (LPG), Deep Multi-Hop Traversal, Cypher | Neo4j (Bolt protocol) | `/neo4j-knowledge-graph-architect` |
| Relational Graph, Hierarchy Trees, Bill of Materials, Pathfinding | Relational SQL (`WITH RECURSIVE`) | `/sql-recursive-graph-traversal` |
| Formal Semantic Ontology, RDF Triples, OWL Reasoning, SPARQL | W3C Semantic Web / Triplestores | `/ontological-engineering-coach` |

---

## Executable Substrate Tooling (`scripts/`)

| Script / Tool | CLI Invocations | Primary Responsibility |
| :--- | :--- | :--- |
| [`cypher_linter.py`](scripts/cypher_linter.py) | `python scripts/cypher_linter.py --query "..."` | Static safety gate: catches unbounded hops, trail semantics traps, and MERGE violations. |
| [`evidence_model.py`](scripts/evidence_model.py) | `python scripts/evidence_model.py --validate data.json` | Reifies 7-tuple evidence objects $\langle s,p,o,t,\sigma,c,\sigma_{status} \rangle$ with boundary layer validation. |
| [`batch_ingest.py`](scripts/batch_ingest.py) | `python scripts/batch_ingest.py --dry-run --batch data.json` | High-throughput batch pipeline with chunking and double-load idempotency assertion. |


---

## Anti-Pattern Invariants Checklist

- [ ] **Descriptive Relationship Types**: Relationships are named with specific domain verbs (`AUTHORED`, `CITES`), not generic links (`RELATED`).
- [ ] **First-Class Edge Associations**: Entity-to-entity links are modeled as relationships, not embedded array properties.
- [ ] **Bounded Node Sprawl**: Nodes represent independent entities; scalar metrics and transient states are stored as properties.
- [ ] **Single-Key MERGE Isolation**: MERGE statements match on a single unique natural key; mutable properties use ON CREATE/MATCH SET.
- [ ] **Hard Traversal Ceilings**: All variable-length relationships enforce strict upper bounds (e.g., `[*1..4]`).
- [ ] **Trail-Safe Diamond Queries**: Diamond topologies and cycles split expansion steps across WITH boundaries.
- [ ] **Real Container Testing**: Integration tests run against ephemeral Neo4j containers, never in-memory mocks.
- [ ] **Constrained Batch Ingestion**: Ingestion executes via parameterized UNWIND batches sized between 1,000 and 5,000 items.
- [ ] **Temporal Evidence Tracking**: Changing or disputed relationships record timestamps, sources, and confidence metrics.
- [ ] **Fact-Inference Boundary**: Inferred relationships and algorithmic scores are tagged explicitly with derivation metadata.
