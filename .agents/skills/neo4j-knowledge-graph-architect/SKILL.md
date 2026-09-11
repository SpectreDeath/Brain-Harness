---
name: neo4j-knowledge-graph-architect
description: Architect, ingest, query, and test production Neo4j property graphs (LPG) using backward schema modeling, idempotent batch ingestion, and traversal safety. Trigger for Neo4j graphs, Cypher queries, or epistemic graphs. Do not use for W3C RDF/OWL (use /ontological-engineering-coach) or SQL CTEs (use /sql-recursive-graph-traversal).
---

# Neo4j Knowledge Graph Architect

`neo4j-knowledge-graph-architect` operationalizes Neo4j as an enterprise-grade Labeled Property Graph (LPG) platform. It provides end-to-end guidance for schema design, idempotent batch ingestion, Cypher query engineering, index governance, and ephemeral integration testing. It incorporates epistemic browsing patterns, temporal evidence modeling, and strict boundaries separating primary graph facts from derived analytical inferences.

```
[1. Schema Design & Semantic Modeling] 
       ↓
[2. Idempotent Batch Ingestion Engine] 
       ↓
[3. Cypher Query Engineering & Traversal Safety] 
       ↓
[4. Index Governance & Query Profiling] 
       ↓
[5. Ephemeral Test Harnessing & Correctness Validation]
```

See [CARD.md](CARD.md) for the companion summary card, 5-stage matrix, core pillars, and anti-pattern checklist.
See [REFERENCE.md](REFERENCE.md) for production Cypher templates, EXPLAIN profiling scripts, and test harness fixtures.
See [`scripts/`](scripts/) for executable tooling:
- [`scripts/cypher_linter.py`](scripts/cypher_linter.py) — Static Cypher safety analyzer (detects unbounded traversals, trail traps, MERGE mutations).
- [`scripts/evidence_model.py`](scripts/evidence_model.py) — Slotted 7-tuple temporal evidence reification engine (Rule 12).
- [`scripts/batch_ingest.py`](scripts/batch_ingest.py) — High-throughput batch ingestion pipeline with chunking and double-load idempotency verification.
Consult `/data-topology-mapper` for structural blast radius mapping and `/epistemic-isnad-audit` for chain-of-custody lineage.

---

## Disambiguation: Graph Engine Selection

Before architecting a graph solution, route the domain problem to the appropriate engineering paradigm:

| Requirement / Paradigm | Engine / Technology | Dispatched Skill |
| :--- | :--- | :--- |
| **Labeled Property Graph (LPG)**: Deep traversal, index-free adjacency, rich node/relationship properties, Cypher queries, pattern matching. | **Neo4j** (Bolt protocol) | `/neo4j-knowledge-graph-architect` (This Skill) |
| **Relational Graph / Hierarchy**: Direct trees, bill of materials, org charts, pathfinding inside existing PostgreSQL / SQLite databases. | **Relational SQL** (`WITH RECURSIVE`) | `/sql-recursive-graph-traversal` |
| **Formal Ontology & Reasoning**: W3C standards, RDF triples, OWL taxonomies, SPARQL endpoints, open-world description logics. | **RDF / Triplestores** | `/ontological-engineering-coach` |

---

## 1. Schema Design & Semantic Modeling

Design labeled property graph schemas **backwards from competency questions**, ensuring every node label, relationship type, and property serves an explicit query need:

1. **Partition Graph Primitives**:
   - **Nodes (`:` Label)**: Model distinct business or epistemic entities with independent lifecycles (`Person`, `Paper`, `Claim`, `Institution`).
   - **Properties (`key: value`)**: Store scalar attributes, metrics, timestamps, and textual descriptions on nodes or edges.
   - **Relationships (`-[:TYPE]->`)**: Model directed semantic connections as explicit, typed verbs (`AUTHORED`, `CITES`, `AFFILIATED_WITH`, `REFUTES`).
2. **Apply Backward Competency Modeling**:
   - Formulate target business/epistemic questions first (e.g., *"Which authors published papers refuting claim X between 2024 and 2026?"*).
   - Derive the path pattern directly from the question: `(:Author)-[:AUTHORED]->(:Paper)-[:REFUTES]->(:Claim)`.
   - Validate that relationship directions reflect the semantic action flow while remaining navigable in either direction during query time.
3. **Model Temporal Evidence Objects**:
   - For contested, dynamic, or empirical domains, do not use flat timeless edges.
   - Reify the connection into a 7-tuple temporal evidence object: `(subject, predicate, object, time, source, confidence, status)`.
   - Represent disputed claims with explicit properties (`confidence: 0.85`, `valid_from: date("2025-01-01")`, `status: "VERIFIED"`).
4. **Enforce the Relation-vs-Inference Boundary**:
   - Separate **documented primary facts** (direct observations from source literature) from **derived graph analytics** (community clusters, inferred links, PageRank scores).
   - Tag inferred edges with distinct types or metadata (`inferred: true`, `algorithm: "louvain"`, `run_id: "20260907"`) to prevent circular hallucinations.

### Axis 3 Diagnostic Questions (Schema Design)
- *What specific business or analytical competency questions must this graph answer on day one?*
- *Have all entities with independent identities been isolated as nodes rather than serialized arrays in properties?*
- *Are relationship types semantically specific verbs (`AUTHORED`, `SUPPORTS`) rather than generic links (`CONNECTED_TO`, `RELATED`)?*
- *Does the schema distinguish primary observational facts from derived algorithmic inferences?*

> **Completion Criterion**: Annotated schema diagram or Cypher schema contract answering all target competency questions, with unambiguous node/relationship partitions and temporal evidence properties.

---

## 2. Idempotent Batch Ingestion Engine

Construct high-throughput, restart-safe data ingestion pipelines utilizing parameterized batches and schema constraints:

1. **Pre-Create Schema Constraints**:
   - Always declare uniqueness and existence constraints before loading data:
     ```cypher
     CREATE CONSTRAINT cst_person_id IF NOT EXISTS
     FOR (p:Person) REQUIRE p.id IS UNIQUE;
     CREATE CONSTRAINT cst_paper_doi IF NOT EXISTS
     FOR (p:Paper) REQUIRE p.doi IS UNIQUE;
     ```
   - Schema constraints automatically back properties with underlying range indexes, accelerating `MERGE` lookups from $O(N)$ scans to $O(\log N)$ seeks.
2. **Enforce Single Driver Instance Lifecycle**:
   - Instantiate exactly one `GraphDatabase.driver` instance per application lifecycle.
   - Manage connection pools through lightweight, short-lived sessions (`driver.session()`) and execute writes inside explicit transaction functions (`session.execute_write(tx_fn)`).
3. **Execute Parameterized Cypher Exclusively**:
   - Never use Python string interpolation or f-strings to inject values into Cypher queries.
   - Pass row batches as structured query parameters (`$batch`) to enable query plan caching and eliminate Cypher injection vulnerabilities.
4. **Implement Identity-Isolated `MERGE`**:
   - Scope `MERGE` statements to a single immutable natural identity property.
   - Set mutable attributes inside `ON CREATE SET` and `ON MATCH SET` clauses:
     ```cypher
     UNWIND $batch AS row
     MERGE (p:Person {id: row.id})
     ON CREATE SET p.name = row.name, p.created_at = datetime()
     ON MATCH SET p.name = row.name, p.updated_at = datetime();
     ```
5. **Tune Chunk Sizes for Memory Bounding**:
   - Ingest data in chunks of 1,000 to 5,000 items.
   - Keep transaction sizes small enough to avoid Java Virtual Machine (JVM) garbage collection pauses and prevent transaction log memory blowout.

### Axis 3 Diagnostic Questions (Ingestion)
- *Are all `MERGE` target properties protected by unique schema constraints before batch execution begins?*
- *Is the ingestion query fully parameterized, with zero string interpolation or concatenated values?*
- *Does each `MERGE` isolate a single immutable natural key, setting other fields via `ON CREATE SET` / `ON MATCH SET`?*
- *Is the batch size tuned between 1,000 and 5,000 rows to ensure sub-second commit cycles?*

> **Completion Criterion**: Executable Python ingestion script processing structured batches via `UNWIND $batch` with identity-isolated `MERGE`, completing double-runs with zero duplicate nodes or relationships.

---

## 3. Cypher Query Engineering & Traversal Safety

Author declarative Cypher queries that leverage index-free adjacency while preventing combinatorial explosion and memory exhaustion:

1. **Anchor Queries & Directional Traversal**:
   - Anchor graph traversals on indexed start nodes using specific labels and property predicates:
     ```cypher
     MATCH (p:Person {id: $person_id})-[:AUTHORED]->(paper:Paper)
     RETURN paper.title, paper.year;
     ```
2. **Mitigate the Cypher Trail Semantics Trap**:
   - **Neo4j Trail Semantics Rule**: A single path pattern will never traverse the exact same relationship twice.
   - *Trap*: In diamond patterns (`(a)-[:REL]->(b)-[:REL]->(d)` and `(a)-[:REL]->(c)-[:REL]->(d)`) or cyclic expansions, queries expecting to traverse shared edges across parallel paths may return zero rows if written as a single chained match.
   - *Mitigation*: Split traversal steps across `WITH` clauses to reset relationship evaluation scopes:
     ```cypher
     MATCH (a:Node {id: $id})-[:STEP1]->(b:Node)
     WITH a, b
     MATCH (b)-[:STEP2]->(c:Node)
     RETURN a, b, c;
     ```
3. **Bound Variable-Length Relationship Traversal**:
   - Never write unbounded path patterns (`-[:CONNECTED*]->`).
   - Always declare explicit lower and upper bounds: `-[:CITES*1..4]->`.
   - Add inline filtering predicates or depth brakes to prevent factorial path explosions on dense nodes.
4. **Apply `OPTIONAL MATCH` Semantics**:
   - Use `OPTIONAL MATCH` for graph outer joins (e.g., retrieving an author whose affiliations may not yet be recorded).
   - Place required graph anchors in the leading `MATCH` before introducing `OPTIONAL MATCH` branches to prevent full-graph scans.
5. **Manage Pipeline Scope via `WITH`**:
   - Use `WITH` to group, aggregate, filter, and page (`ORDER BY`, `SKIP`, `LIMIT`) intermediate rows before expanding to subsequent hops.

### Axis 3 Diagnostic Questions (Query Engineering)
- *Does every variable-length relationship traversal specify an explicit upper bound (e.g., `*1..4`)?*
- *Are multi-hop diamond or cyclic traversals properly split across `WITH` boundaries to avoid trail semantics row drops?*
- *Are optional relationships isolated in `OPTIONAL MATCH` clauses following indexed root anchors?*
- *Are intermediate result sets pruned with `WITH ... WHERE ...` before secondary expansions?*

> **Completion Criterion**: Cypher queries executing with bounded path depths, correct trail semantics handling, and verified deterministic result sets across test graph topologies.

---

## 4. Index Governance & Query Profiling

Govern Neo4j index structures and profile Cypher execution plans to eliminate bottlenecks before production deployment:

1. **Deploy Specialized Index Types**:
   - **Range Index**: Default B-tree index for exact matches and scalar comparisons (`n.id`, `n.age > 30`).
   - **Text Index**: Optimized for substring and regex lookups (`n.name STARTS WITH 'Dr.'`).
   - **Point Index**: Optimized for 2D/3D spatial coordinate queries (`distance(n.location, $point) < 1000`).
   - **Fulltext Index**: Lucene-backed full-text search across multiple node labels and string properties.
   - **Vector Index**: Approximate Nearest Neighbor (ANN) index for high-dimensional embeddings.
2. **Execute `EXPLAIN` in CI Quality Gates**:
   - Run `EXPLAIN` on all query templates during static testing.
   - Verify that queries use `NodeIndexSeek` or `NodeUniqueIndexSeek` rather than full `NodeByLabelScan` or `AllNodesScan`.
   - Fail CI pipelines if any plan contains an unexpected `CartesianProduct` operator.
3. **Profile Execution Plans via `PROFILE`**:
   - Run `PROFILE` on staging environments to inspect actual row counts and database hits (`dbHits`).
   - Read execution plans from the bottom up:
     ```
     ProduceResults
          ↑
        Filter
          ↑
      Expand(All)
          ↑
     NodeIndexSeek
     ```
   - Ensure the ratio of `dbHits` to returned rows remains linear ($O(k)$) rather than quadratic ($O(N^2)$).

### Axis 3 Diagnostic Questions (Index & Profiling)
- *Are query starting nodes resolving via `NodeIndexSeek` or `NodeUniqueIndexSeek`?*
- *Does any query plan contain an unconstrained `CartesianProduct`?*
- *Is the total number of `dbHits` proportional to the returned subgraph rather than the entire database size?*
- *Are text, spatial, and vector searches backed by their respective dedicated index types?*

> **Completion Criterion**: Documented `PROFILE` execution plan showing zero Cartesian products, verified index seek operators on anchor nodes, and bounded `dbHits` metrics.

---

## 5. Ephemeral Test Harnessing & Correctness Validation

Validate graph data pipelines and Cypher queries against real ephemeral database instances:

1. **Enforce Real Database Integration**:
   - Never rely on in-memory mock libraries (such as mock Neo4j drivers) to validate graph queries.
   - Spin up real ephemeral Neo4j containers using `Testcontainers` (Python: `testcontainers-neo4j`) or local Docker instances (`neo4j:5-community`).
2. **Wipe Graph State Between Test Cases**:
   - Implement teardown fixtures executing `MATCH (n) DETACH DELETE n` to guarantee isolation between unit tests.
3. **Execute the Double-Load Idempotency Gate**:
   - Load sample dataset once; record node count $N_1$ and relationship count $R_1$.
   - Load identical sample dataset a second time; record counts $N_2$ and $R_2$.
   - Assert $N_1 == N_2$ and $R_1 == R_2$ to confirm total ingestion idempotency.
4. **Assert Structural and Epistemic Invariants**:
   - Verify property types, date parsing, constraint violation handling, and path reachability across known edge topologies.

### Axis 3 Diagnostic Questions (Testing)
- *Is integration testing conducted against an actual Neo4j instance rather than driver mocks?*
- *Do test suites verify that running batch ingestion twice produces zero duplicate nodes or edges?*
- *Does the teardown fixture clean up all nodes and relationships between test runs?*
- *Are unique constraint violations explicitly tested and handled gracefully?*

> **Completion Criterion**: Passing pytest test suite validating schema creation, idempotent batch loading, query correctness, and constraint enforcement against an ephemeral Neo4j container.

---

## Visual Brief & Architectural Seams

During complex graph modeling or refactoring workflows, generate an interactive visual brief in the `%TEMP%` directory (e.g. `%TEMP%\book-to-skill-forge-*.html`). The brief must contain:
1. Mermaid diagram of the target graph schema (Node labels, Relationship types, Key properties).
2. Competency question matrix mapping queries to Cypher path expressions.
3. Index coverage and constraint definitions.
4. Epistemic evidence boundaries separating primary facts from derived inferences.

---

## Mandatory Checkpoint & Plan Submission

Before executing mutating Cypher scripts, schema drops, or database migrations:
1. Submit an `implementation_plan.md` artifact specifying the planned schema modifications, migration scripts, and rollback procedures.
2. Mark the plan with `RequestFeedback: true`.
3. Halt execution and await explicit user review and approval before mutating persistent graph stores.

---

## In-File Reference: Core Graph Vocabulary

- **Index-Free Adjacency (IFA)**: The core storage architecture where nodes maintain direct physical memory pointers to their adjacent relationships and neighbors, allowing traversals to execute in $O(k)$ time relative to degree $k$, independent of total graph size $N$.
- **Trail Semantics**: Neo4j's graph traversal rule specifying that within a single path pattern, no relationship can be traversed more than once.
- **Hop Count**: The distance or number of relationship edges traversed between two nodes in a graph path.
- **Bolt Protocol**: The binary network protocol operating over TCP or WebSockets used for high-performance communication between client drivers and the Neo4j database engine.
- **dbHits**: Neo4j execution metric representing the discrete storage engine operations required to retrieve or update an entity, property, or pointer.
- **Anchor Query**: The initial matching clause that leverages an index or unique identifier to pinpoint the root nodes from which graph traversal begins.

---

## Anti-Patterns

- **Generic Relationship Stagnation** — Use descriptive, semantically rich relationship types (`AUTHORED`, `VALIDATED_BY`, `CHALLENGES`) rather than generic links (`CONNECTED_TO`, `RELATED`).
- **Connection as Property Anti-Pattern** — Model entity-to-entity associations as first-class directed relationships rather than embedding foreign ID arrays or serialized lists inside node properties.
- **Everything as Node Sprawl** — Restrict nodes to entities with independent identity, lifecycle, or multi-edge connectivity; model scalar metadata, metrics, and timestamps as properties.
- **Compound MERGE Duplicate Explosion** — Scope `MERGE` statements to a single immutable natural identity key, moving mutable properties to explicit `ON CREATE SET` and `ON MATCH SET` clauses.
- **Unbounded Traversal Blowout** — Enforce strict upper path bounds (`[*1..4]`) and filtering predicates on all variable-length graph traversals to protect query memory and prevent server crashes.
- **Relationship Uniqueness Silent Drop** — Split cyclic or diamond traversals across separate `MATCH ... WITH ... MATCH` clauses when edges must be revisited across different paths, circumventing Cypher trail semantics traps.
- **Mock Database Testing Mirage** — Validate graph schema, Cypher syntax, and constraint enforcement against real ephemeral Neo4j containers rather than in-memory mocks that mask driver and query execution errors.
- **Unconstrained Transaction OOM** — Ingest large graph datasets via parameterized `UNWIND $batch` transactions in chunks of 1,000 to 5,000 items rather than opening monolithic gigabyte-scale write transactions.
- **Timeless Relationship Fallacy** — Model relationship lifecycles using explicit valid-time timestamps, versions, or reified temporal evidence objects rather than assuming static, permanent edges.
- **Relation-Inference Conflation** — Maintain strict boundary layers separating primary observed facts from derived graph analytics, marking hypotheses with confidence scores and evidence status.
