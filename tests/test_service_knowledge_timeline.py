"""Tests for temporal timeline layer, dynamic GEXF, and HTML timeline scrubber."""

from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from click.testing import CliRunner

from harness.commands.reflection import knowledge_group
from harness.services.storage.vault_exporters import export_gexf, export_html
from harness.services.storage.vault_graph_models import (
    DerivedKnowledgeGraph,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    KnowledgeGraphSummary,
)


@pytest.fixture
def sample_temporal_graph() -> DerivedKnowledgeGraph:
    nodes = (
        KnowledgeGraphNode(
            id="ki-1",
            label="Item 1",
            domain="developer_experience",
            created_at="2026-08-21T10:00:00Z",
            status="ACTIVE",
        ),
        KnowledgeGraphNode(
            id="ki-2",
            label="Item 2",
            domain="agent_orchestration",
            created_at="2026-09-01T12:00:00Z",
            status="SUPERSEDED",
        ),
    )
    edges = (
        KnowledgeGraphEdge(
            source="ki-1",
            target="ki-2",
            type="supersedes",
            derived=False,
            confidence=1.0,
        ),
    )
    summary = KnowledgeGraphSummary(
        total_nodes=2,
        ki_nodes=2,
        non_ki_nodes_by_kind={},
        total_edges=1,
        edges_by_type={"supersedes": 1},
        derived_edge_count=0,
        asserted_edge_count=1,
        component_count=1,
        largest_component_size=2,
        isolated_ki_count=0,
        untagged_ki_count=0,
        uncategorized_ki_count=0,
        excluded_mega_tags=(),
        date_coverage_count=2,
    )
    return DerivedKnowledgeGraph(nodes=nodes, edges=edges, summary=summary)


def test_export_gexf_dynamic_mode(tmp_path: Path, sample_temporal_graph: DerivedKnowledgeGraph) -> None:
    out_file = tmp_path / "dynamic.gexf"
    export_gexf(sample_temporal_graph, out_file, dynamic=True)

    tree = ET.parse(out_file)
    root = tree.getroot()

    # Find <graph> tag
    graph_elem = root.find("{http://www.gexf.net/1.3draft}graph")
    assert graph_elem is not None
    assert graph_elem.get("mode") == "dynamic"
    assert graph_elem.get("timeformat") == "date"

    # Find nodes
    nodes_elem = graph_elem.find("{http://www.gexf.net/1.3draft}nodes")
    assert nodes_elem is not None
    nodes = list(nodes_elem)
    assert len(nodes) == 2

    # Verify start date
    ki1 = next(n for n in nodes if n.get("id") == "ki-1")
    assert ki1.get("start") == "2026-08-21"

    # Verify superseded end date
    ki2 = next(n for n in nodes if n.get("id") == "ki-2")
    assert ki2.get("start") == "2026-09-01"
    assert ki2.get("end") == "2026-09-01"


def test_export_html_timeline_scrubber(tmp_path: Path, sample_temporal_graph: DerivedKnowledgeGraph) -> None:
    out_file = tmp_path / "timeline.html"
    export_html(sample_temporal_graph, out_file)

    content = out_file.read_text(encoding="utf-8")
    assert "time-slider" in content
    assert "play-btn" in content
    assert "distinctDates" in content
    assert "time-val" in content


def test_cli_knowledge_timeline(tmp_path: Path) -> None:
    vault_dir = tmp_path / "knowledge"
    vault_dir.mkdir(parents=True)

    for item_id, title, dt in [
        ("k1", "Title 1", "2026-08-21T10:00:00Z"),
        ("k2", "Title 2", "2026-08-28T10:00:00Z"),
        ("k3", "Title 3", "2026-09-05T10:00:00Z"),
    ]:
        item_dir = vault_dir / item_id
        item_dir.mkdir()
        meta = {
            "id": item_id,
            "title": title,
            "category": "developer_experience",
            "tags": ["test"],
            "created_at": dt,
        }
        (item_dir / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
        (item_dir / "summary.md").write_text("# Summary", encoding="utf-8")

    runner = CliRunner()
    res = runner.invoke(knowledge_group, ["timeline", "--vault", str(vault_dir)])
    assert res.exit_code == 0
    assert "Total Vault Items:       3" in res.output
    assert "Dated Items:             3 / 3 (100.0%)" in res.output
    assert "Domain Emergence Order" in res.output
    assert "Weekly Creation Velocity" in res.output

    res_json = runner.invoke(knowledge_group, ["timeline", "--vault", str(vault_dir), "--json"])
    assert res_json.exit_code == 0
    data = json.loads(res_json.output)
    assert data["total_items"] == 3
    assert data["dated_items"] == 3
    assert len(data["weekly_growth"]) >= 2

