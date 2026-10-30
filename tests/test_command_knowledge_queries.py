"""Contract test suite for Headless CLI graph queries and MCP resources (Rule 10, Rule 55)."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
import pytest

from harness.commands.reflection import (
    knowledge_dependents,
    knowledge_neighbors,
    knowledge_orphans,
    knowledge_path,
    knowledge_stats,
    knowledge_topic,
)
from harness.mcp.server.registry import MCPRegistry
from harness.services.storage import (
    DerivedKnowledgeGraph,
    KnowledgeEdge,
    KnowledgeGraphEdge,
    KnowledgeGraphNode,
    KnowledgeGraphQueryService,
    KnowledgeGraphSummary,
    KnowledgeItemRecord,
    bfs_shortest_path,
    find_node_neighbors,
    find_vault_orphans,
)
from harness.services.tools import ToolRegistry


@pytest.fixture
def fixture_query_vault(tmp_path: Path) -> Path:
    """Fixture vault containing connected component and an isolated orphan."""
    vault_dir = tmp_path / ".harness" / "knowledge"
    vault_dir.mkdir(parents=True)

    # Node A: Architecture pattern
    ki_a = vault_dir / "ki_alpha"
    ki_a.mkdir()
    (ki_a / "metadata.json").write_text(json.dumps({
        "id": "ki_alpha",
        "title": "Alpha Architecture Service",
        "category": "developer_experience/architecture",
        "tags": ["arch", "service"],
        "source_target": "src/harness/service.py",
        "edges": [
            {"type": "became_skill", "target": "agent-architect", "target_kind": "skill", "derived": False, "confidence": 1.0},
            {"type": "references_code", "target": "src/harness/service.py", "target_kind": "path", "derived": True, "confidence": 0.95},
        ],
    }), encoding="utf-8")
    (ki_a / "summary.md").write_text("Alpha summary", encoding="utf-8")

    # Node B: Peer connected to Node A via same_domain
    ki_b = vault_dir / "ki_beta"
    ki_b.mkdir()
    (ki_b / "metadata.json").write_text(json.dumps({
        "id": "ki_beta",
        "title": "Beta Architecture Router",
        "category": "developer_experience/architecture",
        "tags": ["arch", "service", "router"],
        "edges": [
            {"type": "same_domain", "target": "ki_alpha", "target_kind": "ki", "derived": True, "confidence": 0.80},
        ],
    }), encoding="utf-8")
    (ki_b / "summary.md").write_text("Beta summary", encoding="utf-8")

    # Node C: Disconnected orphan (untagged, uncategorized, missing source)
    ki_c = vault_dir / "ki_orphan"
    ki_c.mkdir()
    (ki_c / "metadata.json").write_text(json.dumps({
        "id": "ki_orphan",
        "title": "Unlinked Stray Note",
        "category": "general",
        "tags": [],
        "edges": [],
    }), encoding="utf-8")
    (ki_c / "summary.md").write_text("Orphan summary", encoding="utf-8")

    return vault_dir


@pytest.mark.unit
class TestKnowledgeQueriesAndTraversalAlgorithms:
    """Verifies BFS reachability, Rule 55 invariant, and neighbor traversal."""

    def test_bfs_shortest_path_and_rule_55_reachability(self) -> None:
        """Verify Rule 55: reachability is strict; no synthetic edges on disconnected nodes."""
        nodes = (
            KnowledgeGraphNode(id="ki_1", label="KI 1"),
            KnowledgeGraphNode(id="ki_2", label="KI 2"),
            KnowledgeGraphNode(id="ki_3", label="KI 3"),
            KnowledgeGraphNode(id="ki_isolated", label="Isolated"),
        )
        edges = (
            KnowledgeGraphEdge(source="ki_1", target="ki_2", type="references_code", derived=False),
            KnowledgeGraphEdge(source="ki_2", target="ki_3", type="became_skill", derived=False),
        )
        summary = KnowledgeGraphSummary(
            total_nodes=4, ki_nodes=4, non_ki_nodes_by_kind={}, total_edges=2,
            edges_by_type={}, derived_edge_count=0, asserted_edge_count=2,
            component_count=2, largest_component_size=3, isolated_ki_count=1,
            untagged_ki_count=0, uncategorized_ki_count=0,
        )
        graph = DerivedKnowledgeGraph(nodes=nodes, edges=edges, summary=summary)

        # 1. Existing path: ki_1 -> ki_3 (2 hops)
        res_found = bfs_shortest_path("ki_1", "ki_3", graph)
        assert res_found["status"] == "found"
        assert res_found["length"] == 2
        assert res_found["chain"] == ["ki_1", "ki_2", "ki_3"]
        assert len(res_found["hops"]) == 2

        # 2. Same node (0 hops)
        res_same = bfs_shortest_path("ki_1", "ki_1", graph)
        assert res_same["status"] == "same_node"
        assert res_same["length"] == 0

        # 3. Disconnected node (Rule 55: MUST return no_path with empty chain)
        res_no_path = bfs_shortest_path("ki_1", "ki_isolated", graph)
        assert res_no_path["status"] == "no_path"
        assert res_no_path["length"] == 0
        assert res_no_path["chain"] == []
        assert res_no_path["hops"] == []

    def test_find_node_neighbors_and_filters(self) -> None:
        """Verify neighbor extraction with depth, direction, and edge_type filters."""
        nodes = (
            KnowledgeGraphNode(id="ki_hub", label="Hub"),
            KnowledgeGraphNode(id="agent-architect", label="Skill", node_kind="skill"),
            KnowledgeGraphNode(id="src/harness/core.py", label="Path", node_kind="path"),
        )
        edges = (
            KnowledgeGraphEdge(source="ki_hub", target="agent-architect", type="became_skill", derived=False),
            KnowledgeGraphEdge(source="ki_hub", target="src/harness/core.py", type="references_code", derived=True),
        )
        summary = KnowledgeGraphSummary(
            total_nodes=3, ki_nodes=1, non_ki_nodes_by_kind={}, total_edges=2,
            edges_by_type={}, derived_edge_count=1, asserted_edge_count=1,
            component_count=1, largest_component_size=3, isolated_ki_count=0,
            untagged_ki_count=0, uncategorized_ki_count=0,
        )
        graph = DerivedKnowledgeGraph(nodes=nodes, edges=edges, summary=summary)

        # All neighbors
        all_nbrs = find_node_neighbors("ki_hub", graph, max_depth=1)
        assert len(all_nbrs) == 2

        # Filter by edge_type
        skill_nbrs = find_node_neighbors("ki_hub", graph, max_depth=1, edge_type="became_skill")
        assert len(skill_nbrs) == 1
        assert skill_nbrs[0]["id"] == "agent-architect"

        # Exclude derived
        asserted_nbrs = find_node_neighbors("ki_hub", graph, max_depth=1, exclude_derived=True)
        assert len(asserted_nbrs) == 1
        assert asserted_nbrs[0]["id"] == "agent-architect"


@pytest.mark.unit
class TestKnowledgeQueriesCLICommands:
    """Verifies Click CLI commands for stats, neighbors, path, topic, dependents, and orphans."""

    def test_cli_knowledge_stats(self, fixture_query_vault: Path) -> None:
        runner = CliRunner()
        # Human-readable output
        res = runner.invoke(knowledge_stats, ["--vault", str(fixture_query_vault)])
        assert res.exit_code == 0, res.output
        assert "Knowledge Graph Census Statistics" in res.output
        assert "Total Entities" in res.output

        # JSON output
        res_json = runner.invoke(knowledge_stats, ["--vault", str(fixture_query_vault), "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert "total_nodes" in data
        assert "total_edges" in data

    def test_cli_knowledge_neighbors(self, fixture_query_vault: Path) -> None:
        runner = CliRunner()
        res = runner.invoke(knowledge_neighbors, ["ki_alpha", "--vault", str(fixture_query_vault)])
        assert res.exit_code == 0, res.output
        assert "Neighborhood for 'ki_alpha'" in res.output
        assert "agent-architect" in res.output

    def test_cli_knowledge_path(self, fixture_query_vault: Path) -> None:
        runner = CliRunner()
        # Existing path
        res_found = runner.invoke(knowledge_path, ["ki_beta", "agent-architect", "--vault", str(fixture_query_vault)])
        assert res_found.exit_code == 0, res_found.output
        assert "Shortest path found" in res_found.output
        assert "ki_beta → ki_alpha → agent-architect" in res_found.output

        # Disconnected path (Rule 55)
        res_none = runner.invoke(knowledge_path, ["ki_alpha", "ki_orphan", "--vault", str(fixture_query_vault)])
        assert res_none.exit_code == 0, res_none.output
        assert "No path found" in res_none.output
        assert "Rule 55" in res_none.output

    def test_cli_knowledge_topic(self, fixture_query_vault: Path) -> None:
        runner = CliRunner()
        res = runner.invoke(knowledge_topic, ["architecture", "--vault", str(fixture_query_vault)])
        assert res.exit_code == 0, res.output
        assert "Topic Neighborhood: 'architecture'" in res.output
        assert "ki_alpha" in res.output
        assert "agent-architect" in res.output

    def test_cli_knowledge_dependents(self, fixture_query_vault: Path) -> None:
        runner = CliRunner()
        res = runner.invoke(knowledge_dependents, ["agent-architect", "--vault", str(fixture_query_vault)])
        assert res.exit_code == 0, res.output
        assert "Inbound Dependents for 'agent-architect'" in res.output
        assert "ki_alpha" in res.output

    def test_cli_knowledge_orphans(self, fixture_query_vault: Path) -> None:
        runner = CliRunner()
        res = runner.invoke(knowledge_orphans, ["--vault", str(fixture_query_vault)])
        assert res.exit_code == 0, res.output
        assert "Knowledge Vault Isolated Entity Triage" in res.output
        assert "ki_orphan" in res.output

        res_json = runner.invoke(knowledge_orphans, ["--vault", str(fixture_query_vault), "--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert data["isolated_count"] >= 1
        assert any(item["id"] == "ki_orphan" for item in data["isolated_items"])


@pytest.mark.unit
class TestKnowledgeMCPResources:
    """Verifies Rule 10 MCP resource listing and reading parity."""

    @pytest.mark.asyncio
    async def test_mcp_registry_resource_parity(self) -> None:
        registry = MCPRegistry(tool_registry=ToolRegistry())
        resources = registry.list_resources()
        uris = {r["uri"] for r in resources}

        assert "harness://knowledge/graph" in uris
        assert "harness://knowledge/contradictions" in uris

        # Read harness://knowledge/graph
        res_graph = await registry.read_resource("harness://knowledge/graph")
        assert res_graph is not None
        content, mime = res_graph
        assert mime == "application/json"
        assert "nodes" in content
        assert "edges" in content
        assert "summary" in content

        # Read harness://knowledge/contradictions
        res_conflicts = await registry.read_resource("harness://knowledge/contradictions")
        assert res_conflicts is not None
        conflicts_content, conflicts_mime = res_conflicts
        assert conflicts_mime == "application/json"
        assert isinstance(conflicts_content, list)

