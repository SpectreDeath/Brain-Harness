"""Comprehensive unit and integration tests for Skill Knowledge Graph plugin."""

from __future__ import annotations

from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.kernel.context import ServiceContext
from harness.services.skill_graph import SKILL_GRAPH_KEY, SkillGraphService
from plugins.skill_knowledge_graph.main import (
    SkillGraphPlugin,
    export_skill_graph_visual,
    find_skill_chain,
    get_skill_topology,
    index_skill_catalog,
    query_skill_router,
)
from plugins.skill_knowledge_graph.models import EdgeType, SkillNode, StageNode
from plugins.skill_knowledge_graph.parser import SkillCardParser
from plugins.skill_knowledge_graph.graph import SkillKnowledgeGraph
from harness.cli import main as cli_main


@pytest.mark.unit
class TestSkillKnowledgeGraphParser:
    """Test AST and markdown card parsing capabilities."""

    def test_parse_isolated_skill(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "mock-skill"
        skill_dir.mkdir()

        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: mock-skill\n"
            "description: A mock skill for testing.\n"
            "---\n\n"
            "# Mock Skill Engine\n\n"
            "## 1. Initial Setup\n"
            "Setup the environment.\n\n"
            "> **Completion criterion**: Environment is ready.\n\n"
            "## Anti-Patterns\n"
            "- **Loose Boundaries** — Allowing uncontrolled state leaks.\n",
            encoding="utf-8",
        )

        (skill_dir / "CARD.md").write_text(
            "# Skill Summary Card: `mock-skill`\n\n"
            "```\n"
            "┌────────────────────────────────────────────────────────┐\n"
            "│               SKILL SUMMARY CARD                       │\n"
            "├────────────────────────────────────────────────────────┤\n"
            "│ Name:        mock-skill                                │\n"
            "│ Category:    testing / mock                            │\n"
            "│ Invocation:  /mock-skill                               │\n"
            "│ Trigger:     \"test mock\", \"run mock\"                   │\n"
            "│ Version:     2.1.0                                     │\n"
            "├────────────────────────────────────────────────────────┤\n"
            "│ Target:      Run mock testing workloads deterministically.│\n"
            "└────────────────────────────────────────────────────────┘\n"
            "```\n\n"
            "## Verification Checklist\n"
            "- [ ] **Boundary Guard**: Must verify isolated state.\n",
            encoding="utf-8",
        )

        node = SkillCardParser.parse_directory(skill_dir)
        assert node is not None
        assert node.name == "mock-skill"
        assert node.category == "testing / mock"
        assert node.version == "2.1.0"
        assert node.invocation == "/mock-skill"
        assert "test mock" in node.triggers
        assert len(node.stages) >= 1
        assert node.stages[0].name == "Initial Setup"
        assert "Environment is ready" in node.stages[0].completion_gate
        assert len(node.anti_patterns) == 1
        assert node.anti_patterns[0].name == "Loose Boundaries"
        assert len(node.invariants) == 1
        assert "Boundary Guard" in node.invariants[0].rule


@pytest.mark.unit
class TestSkillKnowledgeGraphEngine:
    """Test directed graph indexing, routing, and pathfinding."""

    def test_indexing_workspace_skills(self) -> None:
        res = index_skill_catalog(".")
        assert res["status"] == "ok"
        assert res["indexed_skills"] >= 4
        assert res["total_nodes"] >= 4
        assert res["total_edges"] > 0
        assert "architecture" in res["categories"] or "data-science / ingestion" in res["categories"] or "data-science / profiling" in res["categories"] or "general" in res["categories"]

    def test_semantic_router_matching(self) -> None:
        index_skill_catalog(".")

        # 1. Questio query
        res_q = query_skill_router("Perform adversarial reflection and top failure mode check", top_k=2)
        assert res_q["status"] == "ok"
        assert len(res_q["matches"]) > 0
        top_skill = res_q["matches"][0]["skill_name"]
        assert top_skill == "questio-reflection"

        # 2. Data Scout query
        res_s = query_skill_router("fetch structured dataset from UCI repository", top_k=2)
        assert res_s["status"] == "ok"
        assert len(res_s["matches"]) > 0
        assert any(m["skill_name"] == "structured-data-scout" for m in res_s["matches"])

        # 3. Data Topology query
        res_t = query_skill_router("profile dataset distributions and statistical moments", top_k=2)
        assert res_t["status"] == "ok"
        assert any(m["skill_name"] == "data-topology-mapper" for m in res_t["matches"])

    def test_find_skill_chain(self) -> None:
        index_skill_catalog(".")

        res = find_skill_chain("structured-data-scout", "data-topology-mapper")
        assert res["status"] == "ok"
        assert res["chain"] == ["structured-data-scout", "data-topology-mapper"]

        # Longer chain
        res_long = find_skill_chain("structured-data-scout", "questio-reflection")
        if res_long["status"] == "ok":
            assert res_long["chain"][0] == "structured-data-scout"
            assert res_long["chain"][-1] == "questio-reflection"

    def test_get_skill_topology(self) -> None:
        index_skill_catalog(".")

        topo_res = get_skill_topology("questio-reflection")
        assert topo_res["status"] == "ok"
        topo = topo_res["topology"]
        assert topo["skill"]["name"] == "questio-reflection"
        assert len(topo["mitigated_anti_patterns"]) > 0

    def test_export_visual_brief(self, tmp_path: Path) -> None:
        index_skill_catalog(".")
        out_html = tmp_path / "skill_graph_test.html"

        res = export_skill_graph_visual(str(out_html))
        assert res["status"] == "ok"
        assert out_html.exists()

        content = out_html.read_text(encoding="utf-8")
        assert "Agent Skill Knowledge Graph" in content
        assert "mermaid" in content
        assert "questio-reflection" in content
        assert "structured-data-scout" in content


@pytest.mark.unit
class TestSkillKnowledgeGraphServiceAndCLI:
    """Test IoC service integration and CLI commands."""

    @pytest.mark.asyncio
    async def test_plugin_lifecycle_and_ioc(self) -> None:
        ctx = ServiceContext()
        plugin = SkillGraphPlugin()

        await plugin.on_load(ctx)
        service = ctx.require(SKILL_GRAPH_KEY)
        assert service is not None

        await plugin.on_enable()
        chain = await service.find_chain("structured-data-scout", "data-topology-mapper")
        assert len(chain) == 2

    def test_cli_skills_graph_and_route(self) -> None:
        runner = CliRunner()

        # Test harness skills graph
        result_graph = runner.invoke(cli_main, ["skills", "graph", "--path", "."])
        assert result_graph.exit_code == 0
        assert "Indexed" in result_graph.output

        # Test harness skills route
        result_route = runner.invoke(cli_main, ["skills", "route", "audit isnad lineage of claims"])
        assert result_route.exit_code == 0
        assert "Route matches" in result_route.output
        assert "epistemic-isnad-audit" in result_route.output

        # Test harness skills info
        result_info = runner.invoke(cli_main, ["skills", "info", "questio-reflection"])
        assert result_info.exit_code == 0
        assert "Skill: questio-reflection" in result_info.output
