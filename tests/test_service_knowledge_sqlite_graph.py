"""Tests for SQLite recursive CTE graph queries and Cypher batch export (Track 5)."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from click.testing import CliRunner
import pytest

from harness.commands.reflection import knowledge_group
from harness.services.storage.sqlite import SQLiteStorageService
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
    path_res = find_path_sql(conn, "A", "C", max_depth=5, directed=True)
    assert path_res["status"] == "found"
    assert path_res["chain"] == ["A", "B", "C"]
    assert path_res["length"] == 2
    assert len(path_res["hops"]) == 2
    assert path_res["hops"][0]["from"] == "A"
    assert path_res["hops"][0]["to"] == "B"
    assert path_res["hops"][0]["edge_type"] == "synthesizes"
    assert path_res["hops"][0]["direction"] == "forward"

    # 2. Same-node test
    same_res = find_path_sql(conn, "A", "A")
    assert same_res["status"] == "same_node"
    assert same_res["chain"] == ["A"]
    assert same_res["length"] == 0
    assert same_res["hops"] == []

    # 3. Directed vs Undirected
    undirected_res = find_path_sql(conn, "C", "A", max_depth=5, directed=False)
    assert undirected_res["status"] == "found"
    assert undirected_res["chain"] == ["C", "B", "A"]
    assert undirected_res["hops"][0]["direction"] == "reverse"

    directed_rev = find_path_sql(conn, "C", "A", max_depth=5, directed=True)
    assert directed_rev["status"] == "no_path"

    # 4. Strict Rule 55: Disconnected node D to A must return no_path
    no_path = find_path_sql(conn, "D", "A", max_depth=5)
    assert no_path["status"] == "no_path"
    assert no_path["chain"] == []
    assert no_path["length"] == 0

    # 5. Transitive dependents for C: B (depth 1) and A (depth 2)
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


@pytest.mark.asyncio
async def test_sqlite_storage_service_sync_and_cli(tmp_path: Path) -> None:
    # Set up fixture vault
    ki1_dir = tmp_path / "ki-node-1"
    ki1_dir.mkdir(parents=True)
    (ki1_dir / "metadata.json").write_text(
        json.dumps({
            "id": "ki-node-1",
            "title": "Node 1",
            "category": "software_engineering",
            "tags": ["arch"],
            "edges": [{"target": "ki-node-2", "type": "synthesizes", "target_kind": "ki", "confidence": 1.0}],
        }),
        encoding="utf-8",
    )
    (ki1_dir / "summary.md").write_text("Summary 1", encoding="utf-8")

    ki2_dir = tmp_path / "ki-node-2"
    ki2_dir.mkdir(parents=True)
    (ki2_dir / "metadata.json").write_text(
        json.dumps({
            "id": "ki-node-2",
            "title": "Node 2",
            "category": "software_engineering",
            "tags": ["arch"],
            "edges": [{"target": "ki-node-3", "type": "supersedes", "target_kind": "ki", "confidence": 0.9}],
        }),
        encoding="utf-8",
    )
    (ki2_dir / "summary.md").write_text("Summary 2", encoding="utf-8")

    ki3_dir = tmp_path / "ki-node-3"
    ki3_dir.mkdir(parents=True)
    (ki3_dir / "metadata.json").write_text(
        json.dumps({
            "id": "ki-node-3",
            "title": "Node 3",
            "category": "software_engineering",
            "tags": ["arch"],
            "edges": [],
        }),
        encoding="utf-8",
    )
    (ki3_dir / "summary.md").write_text("Summary 3", encoding="utf-8")

    storage = SQLiteStorageService(":memory:")
    count = await storage.sync_knowledge_vault(tmp_path)
    assert count == 3

    # Check that ki_edges was populated
    cursor = storage._ensure_connection().execute("SELECT count(*) FROM ki_edges")
    edge_count = cursor.fetchone()[0]
    assert edge_count >= 2

    # Check storage methods directly
    path_res = storage.find_path_sql("ki-node-1", "ki-node-3")
    assert path_res["status"] == "found"
    assert path_res["chain"] == ["ki-node-1", "ki-node-2", "ki-node-3"]
    assert len(path_res["hops"]) == 2

    deps = storage.get_transitive_dependents_sql("ki-node-3")
    assert len(deps) >= 2
    sources = [d["source_ki"] for d in deps]
    assert "ki-node-2" in sources
    assert "ki-node-1" in sources

    storage.close()

    # CLI path test with --engine sqlite
    runner = CliRunner()
    res = runner.invoke(
        knowledge_group,
        ["path", "ki-node-1", "ki-node-3", "--engine", "sqlite", "-v", str(tmp_path)],
    )
    assert res.exit_code == 0
    assert "ki-node-1 → ki-node-2 → ki-node-3" in res.output

    # CLI dependents test with --transitive
    dep_res = runner.invoke(
        knowledge_group,
        ["dependents", "ki-node-3", "--transitive", "-v", str(tmp_path)],
    )
    assert dep_res.exit_code == 0
    assert "ki-node-2" in dep_res.output
    assert "ki-node-1" in dep_res.output
    assert "(hop 1)" in dep_res.output
    assert "(hop 2)" in dep_res.output

