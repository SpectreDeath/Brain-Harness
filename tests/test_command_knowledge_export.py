"""Unit and CLI contract tests for Knowledge Graph export across all formats (Rule 11, Rule 23, Rule 40)."""

from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

from click.testing import CliRunner
import pytest

from harness.commands.reflection import knowledge_export, knowledge_group
from harness.services.storage import (
    DerivedKnowledgeGraph,
    KnowledgeEdge,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    KnowledgeGraphQueryService,
    KnowledgeGraphSummary,
    KnowledgeItemRecord,
    export_gexf,
    export_graphml,
    export_html,
    export_json,
    export_knowledge_graph,
    validate_export_path,
)


@pytest.fixture
def fixture_graph() -> DerivedKnowledgeGraph:
    """Fixture deterministic derived graph with KIs, skills, code paths, and asserted/derived edges."""
    nodes = (
        KnowledgeGraphNode(
            id="ki_01",
            label="Architecture Pattern",
            node_kind="ki",
            category="developer_experience/architecture",
            domain="developer_experience",
            tags=("pattern", "architecture"),
            status="ACTIVE",
            retrieval_count=5,
            success_count=4,
            created_at="2026-10-30T10:00:00Z",
            source_target="src/harness/core.py",
        ),
        KnowledgeGraphNode(
            id="ki_02",
            label="Storage Decomposition",
            node_kind="ki",
            category="developer_experience/architecture",
            domain="developer_experience",
            tags=("pattern", "architecture", "storage"),
            status="ACTIVE",
            retrieval_count=2,
            success_count=2,
            created_at="2026-10-30T11:00:00Z",
            source_target="src/harness/services/storage/sqlite.py",
        ),
        KnowledgeGraphNode(
            id="agent-architect",
            label="agent-architect",
            node_kind="skill",
            category="agent_orchestration",
            domain="agent_orchestration",
            status="EXTERNAL",
        ),
        KnowledgeGraphNode(
            id="src/harness/core.py",
            label="src/harness/core.py",
            node_kind="path",
            category="developer_experience/architecture",
            domain="developer_experience",
            status="EXTERNAL",
        ),
    )

    edges = (
        KnowledgeGraphEdge(
            source="ki_01",
            target="agent-architect",
            target_kind="skill",
            type="became_skill",
            derived=False,
            confidence=1.0,
            description="Asserted skill lineage",
        ),
        KnowledgeGraphEdge(
            source="ki_01",
            target="src/harness/core.py",
            target_kind="path",
            type="references_code",
            derived=False,
            confidence=0.95,
        ),
        KnowledgeGraphEdge(
            source="ki_01",
            target="ki_02",
            target_kind="ki",
            type="same_domain",
            derived=True,
            confidence=0.80,
            shared_tags=("architecture", "pattern"),
        ),
    )

    summary = KnowledgeGraphSummary(
        total_nodes=4,
        ki_nodes=2,
        non_ki_nodes_by_kind={"skill": 1, "path": 1},
        total_edges=3,
        edges_by_type={"became_skill": 1, "references_code": 1, "same_domain": 1},
        derived_edge_count=1,
        asserted_edge_count=2,
        component_count=1,
        largest_component_size=4,
        isolated_ki_count=0,
        untagged_ki_count=0,
        uncategorized_ki_count=0,
        excluded_mega_tags=("endogenous_memory",),
    )

    return DerivedKnowledgeGraph(nodes=nodes, edges=edges, summary=summary)


@pytest.mark.unit
class TestKnowledgeExporters:
    """Verifies round-trip fidelity, zero dangling edges, and schema compliance across all four formats."""

    def test_export_json_roundtrip(self, fixture_graph: DerivedKnowledgeGraph, tmp_path: Path) -> None:
        out_file = tmp_path / "graph.json"
        written = export_json(fixture_graph, out_file)
        assert written == out_file.resolve()
        assert out_file.exists()

        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert len(data["nodes"]) == 4
        assert len(data["edges"]) == 3
        assert data["summary"]["total_nodes"] == 4
        assert data["summary"]["asserted_edge_count"] == 2
        assert "endogenous_memory" in data["summary"]["excluded_mega_tags"]

        # Verify deterministic node ordering by ID
        node_ids = [n["id"] for n in data["nodes"]]
        assert node_ids == sorted(node_ids)

    def test_export_gexf_zero_dangling_edges_and_attributes(
        self, fixture_graph: DerivedKnowledgeGraph, tmp_path: Path
    ) -> None:
        out_file = tmp_path / "graph.gexf"
        written = export_gexf(fixture_graph, out_file)
        assert written == out_file.resolve()

        tree = ET.parse(out_file)
        root = tree.getroot()
        ns = {"g": "http://www.gexf.net/1.3draft"}

        # Check description in meta
        desc = root.find("g:meta/g:description", ns)
        assert desc is not None and "Derived Knowledge Graph: 4 nodes" in desc.text

        # Extract declared node IDs
        declared_nodes = {n.attrib["id"] for n in root.findall(".//g:node", ns)}
        assert len(declared_nodes) == 4
        assert "ki_01" in declared_nodes
        assert "agent-architect" in declared_nodes

        # Verify edge targets and assert zero dangling references
        edges = root.findall(".//g:edge", ns)
        assert len(edges) == 3
        for e in edges:
            assert e.attrib["source"] in declared_nodes
            assert e.attrib["target"] in declared_nodes
            weight = float(e.attrib["weight"])
            assert 0.0 <= weight <= 1.0

    def test_export_graphml_zero_dangling_edges_and_keys(
        self, fixture_graph: DerivedKnowledgeGraph, tmp_path: Path
    ) -> None:
        out_file = tmp_path / "graph.graphml"
        written = export_graphml(fixture_graph, out_file)
        assert written == out_file.resolve()

        tree = ET.parse(out_file)
        root = tree.getroot()
        ns = {"gm": "http://graphml.graphdrawing.org/xmlns"}

        declared_nodes = {n.attrib["id"] for n in root.findall(".//gm:node", ns)}
        assert len(declared_nodes) == 4

        edges = root.findall(".//gm:edge", ns)
        assert len(edges) == 3
        for e in edges:
            assert e.attrib["source"] in declared_nodes
            assert e.attrib["target"] in declared_nodes

        # Verify key definitions exist for yEd and Cytoscape
        keys = {k.attrib["id"]: k.attrib["attr.type"] for k in root.findall(".//gm:key", ns)}
        assert keys["label"] == "string"
        assert keys["node_kind"] == "string"
        assert keys["confidence"] == "double"
        assert keys["derived"] == "boolean"

    def test_export_html_contains_brief_elements(
        self, fixture_graph: DerivedKnowledgeGraph, tmp_path: Path
    ) -> None:
        out_file = tmp_path / "graph.html"
        written = export_html(fixture_graph, out_file)
        assert written == out_file.resolve()

        content = out_file.read_text(encoding="utf-8")
        assert "<canvas id=\"graph-canvas\"" in content
        assert "id=\"inspector\"" in content
        assert "class=\"mermaid\"" in content
        assert "endogenous_memory" in content
        assert "Total Nodes" in content
        assert "Total Edges" in content
        assert "const DATA =" in content

    def test_export_knowledge_graph_dispatcher(
        self, fixture_graph: DerivedKnowledgeGraph, tmp_path: Path
    ) -> None:
        # Test all valid formats
        for fmt in ("json", "gexf", "graphml", "html"):
            p = export_knowledge_graph(fixture_graph, tmp_path / f"out.{fmt}", format=fmt)
            assert p.exists()

        # Test invalid format raises ValueError
        with pytest.raises(ValueError, match="Unsupported export format 'csv'"):
            export_knowledge_graph(fixture_graph, tmp_path / "out.csv", format="csv")


@pytest.mark.unit
class TestKnowledgeExportCLICommand:
    """Verifies Click CLI command invocation, option handling, and Rule 40 path protection."""

    @pytest.mark.asyncio
    async def test_cli_export_command_execution(self, tmp_path: Path) -> None:
        vault_dir = tmp_path / ".harness" / "knowledge"
        vault_dir.mkdir(parents=True)

        # Create two sample items in vault
        ki1_dir = vault_dir / "ki_alpha"
        ki1_dir.mkdir()
        (ki1_dir / "metadata.json").write_text(json.dumps({
            "id": "ki_alpha",
            "title": "Alpha Service Pattern",
            "category": "developer_experience/architecture",
            "tags": ["arch", "pattern"],
            "source_target": "src/harness/service.py",
        }), encoding="utf-8")
        (ki1_dir / "summary.md").write_text("Alpha summary", encoding="utf-8")

        ki2_dir = vault_dir / "ki_beta"
        ki2_dir.mkdir()
        (ki2_dir / "metadata.json").write_text(json.dumps({
            "id": "ki_beta",
            "title": "Beta Service Pattern",
            "category": "developer_experience/architecture",
            "tags": ["arch", "pattern"],
        }), encoding="utf-8")
        (ki2_dir / "summary.md").write_text("Beta summary", encoding="utf-8")

        runner = CliRunner()

        # 1. Export JSON
        out_json = tmp_path / "exports" / "graph.json"
        res_json = runner.invoke(knowledge_export, [
            "--format", "json",
            "--out", str(out_json),
            "--vault", str(vault_dir),
        ])
        assert res_json.exit_code == 0, res_json.output
        assert "Knowledge Graph Export (JSON)" in res_json.output
        assert out_json.exists()

        # 2. Export GEXF
        out_gexf = tmp_path / "exports" / "graph.gexf"
        res_gexf = runner.invoke(knowledge_export, [
            "--format", "gexf",
            "--out", str(out_gexf),
            "--vault", str(vault_dir),
        ])
        assert res_gexf.exit_code == 0
        assert out_gexf.exists()

        # 3. Export GraphML
        out_graphml = tmp_path / "exports" / "graph.graphml"
        res_graphml = runner.invoke(knowledge_export, [
            "--format", "graphml",
            "--out", str(out_graphml),
            "--vault", str(vault_dir),
        ])
        assert res_graphml.exit_code == 0
        assert out_graphml.exists()

        # 4. Export HTML
        out_html = tmp_path / "exports" / "graph.html"
        res_html = runner.invoke(knowledge_export, [
            "--format", "html",
            "--out", str(out_html),
            "--vault", str(vault_dir),
        ])
        assert res_html.exit_code == 0
        assert out_html.exists()

        # 5. Rule 40 path rejection: target inside vault must fail with error code
        invalid_out = vault_dir / "illegal_export.json"
        res_invalid = runner.invoke(knowledge_export, [
            "--format", "json",
            "--out", str(invalid_out),
            "--vault", str(vault_dir),
        ])
        assert res_invalid.exit_code != 0
        assert "forbidden by Rule 40" in res_invalid.output

