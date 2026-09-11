# Neo4j Knowledge Graph Architect — Reference Implementation Library

This document provides production-ready code templates, Cypher patterns, diagnostic matrices, and testing fixtures for the `neo4j-knowledge-graph-architect` skill.

Executable implementations are located in [`scripts/`](scripts/):
- [`scripts/cypher_linter.py`](scripts/cypher_linter.py): Offline static Cypher safety & trail semantics analyzer
- [`scripts/evidence_model.py`](scripts/evidence_model.py): Slotted 7-tuple temporal evidence object engine (Rule 12)
- [`scripts/batch_ingest.py`](scripts/batch_ingest.py): High-throughput batch ingestion pipeline with idempotency gate


---

## 1. Production Batch Ingestion with UNWIND and Parameters

```python
from typing import Any
from neo4j import GraphDatabase, Driver

def ingest_entity_batch(
    driver: Driver,
    batch_data: list[dict[str, Any]],
    database: str = "neo4j",
) -> int:
    """Ingest a batch of entities idempotently using parameterized UNWIND and identity-isolated MERGE.

    Args:
        driver: Active Neo4j driver instance.
        batch_data: List of dictionaries containing entity attributes.
        database: Target Neo4j database name.

    Returns:
        Number of processed records.
    """
    query = """
    UNWIND $batch AS row
    MERGE (p:Paper {doi: row.doi})
    ON CREATE SET
        p.title = row.title,
        p.year = row.year,
        p.created_at = datetime()
    ON MATCH SET
        p.title = row.title,
        p.year = row.year,
        p.updated_at = datetime()
    
    WITH p, row
    WHERE row.author_id IS NOT NULL
    MERGE (a:Person {id: row.author_id})
    ON CREATE SET
        a.name = row.author_name,
        a.created_at = datetime()
    
    MERGE (a)-[r:AUTHORED]->(p)
    ON CREATE SET
        r.role = coalesce(row.author_role, 'primary'),
        r.created_at = datetime()
    """

    with driver.session(database=database) as session:
        result = session.execute_write(lambda tx: tx.run(query, batch=batch_data).consume())
        return len(batch_data)
```

---

## 2. Trail-Safe WITH-Split Diamond Traversal

```cypher
// Query: Find mutual collaborators who co-authored papers with both Author A and Author B
// Mitigation: Split expansion across WITH to prevent trail semantics row drops

MATCH (a1:Person {id: $author_a})-[:AUTHORED]->(p1:Paper)<-[:AUTHORED]-(collab:Person)
WHERE collab <> a1
WITH DISTINCT a1, collab

MATCH (collab)-[:AUTHORED]->(p2:Paper)<-[:AUTHORED]-(a2:Person {id: $author_b})
WHERE collab <> a2
RETURN collab.name AS mutual_collaborator,
       count(DISTINCT p1) AS papers_with_a,
       count(DISTINCT p2) AS papers_with_b
ORDER BY papers_with_a + papers_with_b DESC
LIMIT 10;
```

---

## 3. Headless EXPLAIN / PROFILE Query Plan Inspector

```python
import json
from neo4j import GraphDatabase

def inspect_query_plan(uri: str, auth: tuple[str, str], cypher_query: str) -> dict:
    """Inspect Cypher query execution plan and detect Cartesian products or full scans."""
    with GraphDatabase.driver(uri, auth=auth) as driver:
        with driver.session() as session:
            # Execute with EXPLAIN prefix
            result = session.run(f"EXPLAIN {cypher_query}")
            summary = result.consume()
            plan = summary.plan

            def walk_plan(operator) -> list[str]:
                ops = [operator.operator_type]
                for child in operator.children:
                    ops.extend(walk_plan(child))
                return ops

            all_operators = walk_plan(plan) if plan else []
            has_cartesian = any("CartesianProduct" in op for op in all_operators)
            has_label_scan = any("NodeByLabelScan" in op or "AllNodesScan" in op for op in all_operators)

            return {
                "operators": all_operators,
                "has_cartesian_product": has_cartesian,
                "has_full_scan": has_label_scan,
                "root_operator": plan.operator_type if plan else None,
            }
```

---

## 4. 5-Symptom Diagnostic Table

| Diagnostic Symptom | Probable Root Cause | Authoritative Engineering Remedy |
| :--- | :--- | :--- |
| **Duplicate Nodes After MERGE** | `MERGE` statement includes mutable properties (e.g. timestamps) in the match pattern. | Isolate `MERGE` to immutable natural key; move mutable attributes to `ON CREATE SET` / `ON MATCH SET`. |
| **Missing Rows on Diamond Paths** | Neo4j Trail Semantics prevents traversing the same relationship twice in one pattern. | Split traversal across `WITH` clauses: `MATCH (a)-[r1]->(b) WITH a, b MATCH (b)-[r2]->(c)`. |
| **Sudden Memory Spike / OOM** | Variable-length path query lacks upper hop bound (`-[:REL*]->`). | Add explicit depth constraints: `-[:REL*1..4]->` and filter intermediate results with `WITH ... LIMIT`. |
| **Slow Ingestion Throughput** | Missing unique constraint on `MERGE` target property, causing full table scans. | Run `CREATE CONSTRAINT ... IS UNIQUE` prior to data ingestion; verify with `SHOW CONSTRAINTS`. |
| **Driver Connection Exhaustion** | Creating new `GraphDatabase.driver` instance per web request or worker thread. | Instantiate a single driver singleton at application bootstrap; open lightweight sessions per transaction. |

---

## 5. Ephemeral Pytest Integration Test Fixture

```python
import pytest
from neo4j import GraphDatabase

@pytest.fixture(scope="session")
def neo4j_driver():
    """Session-scoped Neo4j driver connected to ephemeral test container."""
    uri = "bolt://localhost:7687"
    auth = ("neo4j", "testpassword")
    driver = GraphDatabase.driver(uri, auth=auth)
    yield driver
    driver.close()

@pytest.fixture(autouse=True)
def clean_graph(neo4j_driver):
    """Wipe database before and after each test case to guarantee test isolation."""
    with neo4j_driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    yield
    with neo4j_driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

def test_idempotent_ingestion_double_load(neo4j_driver):
    """Verify that running batch ingestion twice produces zero duplicate entities."""
    sample_batch = [
        {"doi": "10.1000/182", "title": "Knowledge Graph Foundations", "year": 2025, "author_id": "a1", "author_name": "Dr. Ada Lovelace"},
        {"doi": "10.1000/183", "title": "Graph Traversal Invariants", "year": 2026, "author_id": "a1", "author_name": "Dr. Ada Lovelace"},
    ]

    # Pre-create constraint
    with neo4j_driver.session() as session:
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Paper) REQUIRE p.doi IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Person) REQUIRE a.id IS UNIQUE")

    # Ingest Pass 1
    from reference_ingest import ingest_entity_batch
    ingest_entity_batch(neo4j_driver, sample_batch)

    with neo4j_driver.session() as session:
        n_papers_1 = session.run("MATCH (p:Paper) RETURN count(p) AS c").single()["c"]
        n_authors_1 = session.run("MATCH (a:Person) RETURN count(a) AS c").single()["c"]

    # Ingest Pass 2 (Identical Data)
    ingest_entity_batch(neo4j_driver, sample_batch)

    with neo4j_driver.session() as session:
        n_papers_2 = session.run("MATCH (p:Paper) RETURN count(p) AS c").single()["c"]
        n_authors_2 = session.run("MATCH (a:Person) RETURN count(a) AS c").single()["c"]

    # Assert Complete Idempotency
    assert n_papers_1 == 2 and n_papers_2 == 2
    assert n_authors_1 == 1 and n_authors_2 == 1
```
