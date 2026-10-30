"""Tests for SQLite recursive CTE graph queries and Cypher batch export (Track 5)."""

from __future__ import annotations

from pathlib import Path
import sqlite3
import pytest

from harness.services.storage.vault_cypher_exporter import export_cypher
from harness.services.storage.vault_graph_models import (
    DerivedKnowledgeGraph,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    KnowledgeGraphSummary,
)
from harness.services.storage.vault_sqlite_graph import (
    find_path_sql,
    get_transitive_dependents_sql,
    init_ki_edges_table,
    sync_ki_edges,
)


@pytest.fixture
def mock_dag() -> DerivedKnowledgeGraph:
    # A -> B -> C, D (isolated)
    nodes = (
        KnowledgeGraphNode(id="A", label="Node A", node_kind="ki"),
        KnowledgeGraphNode(id="B", label="Node B", node_kind="ki"),
        KnowledgeGraphNode(id="C", label="Node C", node_kind="skill"),
        KnowledgeGraphNode(id="D", label="Node D", node_kind="ki"),
    )
    edges = (
        KnowledgeGraphEdge(source="A", target="B", type="synthesizes", derived=False),
        KnowledgeGraphEdge(source="B", target="C", type="became_skill", derived=False),
    )
    summary = KnowledgeGraphSummary(
        total_nodes=4,
        ki_nodes=3,
        non_ki_nodes_by_kind={"skill": 1},
        total_edges=2,
        edges_by_type={"synthesizes": 1, "became_skill": 1},
        derived_edge_count=0,
        asserted_edge_count=2,
        component_count=2,
        largest_component_size=3,
        isolated_ki_count=1,
        untagged_ki_count=0,
        uncategorized_ki_count=0,
        excluded_mega_tags=(),
        date_coverage_count=4,
    )
    return DerivedKnowledgeGraph(nodes=nodes, edges=edges, summary=summary)


def test_sqlite_recursive_path_and_dependents(mock_dag: DerivedKnowledgeGraph) -> None:
    conn = sqlite3.connect(":memory:")
    init_ki_edges_table(conn)
    synced = sync_ki_edges(conn, mock_dag)
    assert synced == 2

    # 1. Path from A to C: multi-hop A -> B -> C
    path_res = find_path_sql(conn, "A", "C", max_depth=5)
    assert path_res["status"] == "found"
    assert path_res["chain"] == ["A", "B", "C"]
    assert path_res["length"] == 2

    # 2. Strict Rule 55: Disconnected node D to A must return no_path
    no_path = find_path_sql(conn, "D", "A", max_depth=5)
    assert no_path["status"] == "no_path"
    assert no_path["chain"] == []
    assert no_path["length"] == 0

    # 3. Transitive dependents for C: B (depth 1) and A (depth 2)
    deps = get_transitive_dependents_sql(conn, "C", max_depth=5)
    assert len(deps) == 2
    sources = [d["source_ki"] for d in deps]
    assert "B" in sources
    assert "A" in sources
    conn.close()


def test_export_cypher_script(tmp_path: Path, mock_dag: DerivedKnowledgeGraph) -> None:
    out_file = tmp_path / "export.cypher"
    export_cypher(mock_dag, out_file)

    content = out_file.read_text(encoding="utf-8")
    assert "CREATE CONSTRAINT ki_id_unique" in content
    assert 'MERGE (n:KnowledgeItem {id: "A"}' in content
    assert 'MERGE (n:Skill {id: "C"}' in content
    assert 'MERGE (s)-[r:SYNTHESIZES]->(t)' in content
    assert 'MERGE (s)-[r:BECAME_SKILL]->(t)' in content

