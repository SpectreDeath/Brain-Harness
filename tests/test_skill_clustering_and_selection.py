"""Comprehensive test suite for Skill Clustering, Emergent Capabilities, and Intelligent Selection."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from harness.agent.swarm import SwarmCoordinator, SwarmDAG
from harness.cli import main as cli_main
from harness.kernel.context import ServiceContext
from harness.services.skill_clustering import (
    SKILL_CLUSTERING_KEY,
    CrossClusterBridge,
    EmergentCapability,
    SkillCluster,
    SkillClusteringEngine,
    SkillClusteringService,
    SkillSelectionPlan,
)
from harness.services.skill_graph import (
    SKILL_REGISTRY_KEY,
    BuiltinSkillGraphService,
    BuiltinSkillRegistryService,
    SkillRegistryPlugin,
)
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry
from plugins.memory_and_epistemics.skill_knowledge_graph.main import SkillGraphPlugin


@pytest.mark.unit
class TestSkillClusteringEngine:
    """Test the domain clustering and emergent capability engine."""

    def test_cluster_formation_and_cohesion(self) -> None:
        registry = BuiltinSkillRegistryService()
        skills = registry.discover_all(".")
        assert len(skills) >= 10

        engine = SkillClusteringEngine(skills)
        clusters = engine.build_clusters(min_cluster_size=2)

        # Degree dampening prevents single-blob collapse; should have multiple clusters
        assert len(clusters) >= 8
        for c in clusters:
            assert isinstance(c, SkillCluster)
            assert len(c.skills) >= 2
            assert 0.0 <= c.cohesion_score <= 1.0
            assert c.dominant_category
            assert c.central_hub_skill in c.skills

    def test_emergent_capability_discovery(self) -> None:
        registry = BuiltinSkillRegistryService()
        skills = registry.discover_all(".")
        engine = SkillClusteringEngine(skills)

        capabilities = engine.discover_emergent_capabilities()
        assert len(capabilities) >= 3

        for cap in capabilities:
            assert isinstance(cap, EmergentCapability)
            assert cap.name
            assert cap.description
            assert len(cap.composed_skills) >= 2
            assert cap.synergy_score > 0.0
            assert cap.novelty_type in {"cross-cluster-pipeline", "cluster-synthesis", "canonical-pipeline"}

        # Test query filtering
        vault_caps = engine.discover_emergent_capabilities(query="vault")
        assert any("vault" in c.name.lower() or "vault" in c.description.lower() for c in vault_caps)

    def test_detect_cross_cluster_bridges(self) -> None:
        registry = BuiltinSkillRegistryService()
        skills = registry.discover_all(".")
        engine = SkillClusteringEngine(skills)

        bridges = engine.detect_cross_cluster_bridges()
        assert len(bridges) > 0

        for b in bridges:
            assert isinstance(b, CrossClusterBridge)
            assert b.source_skill != b.target_skill
            assert b.source_cluster != b.target_cluster
            assert b.bridge_weight > 0.0

    def test_select_skills_for_task(self) -> None:
        registry = BuiltinSkillRegistryService()
        skills = registry.discover_all(".")
        engine = SkillClusteringEngine(skills)

        plan = engine.select_skills_for_task(
            "modernize legacy codebase and map dependencies safely",
            max_skills=4,
            include_verifier=True,
        )

        assert isinstance(plan, SkillSelectionPlan)
        assert plan.task == "modernize legacy codebase and map dependencies safely"
        assert len(plan.matched_skills) > 0
        assert len(plan.ordered_pipeline) > 0
        assert len(plan.clusters_involved) > 0

        # Should include relevant legacy skills
        assert any("legacy" in s for s in plan.ordered_pipeline)

        # Stages must have completion gates
        assert len(plan.stages) > 0
        assert all("completion_gate" in st for st in plan.stages)
        assert all(st["completion_gate"] for st in plan.stages)

        # Verifier should be included when requested
        assert plan.tail_verifier == "adversarial-agent-verifier"


@pytest.mark.unit
class TestBuiltinSkillRegistryClustering:
    """Test clustering, discovery, and selection integration in BuiltinSkillRegistryService."""

    def test_registry_clustering_delegation(self) -> None:
        registry = BuiltinSkillRegistryService()

        clusters = registry.cluster_skills(min_cluster_size=2)
        assert len(clusters) >= 8

        caps = registry.discover_emergent_capabilities()
        assert len(caps) >= 3

        bridges = registry.get_cross_cluster_bridges()
        assert len(bridges) > 0

        plan = registry.select_skills_for_task("ingest video transcript into verified knowledge vault")
        assert len(plan.ordered_pipeline) >= 2
        assert plan.confidence > 0.0
        assert len(plan.stages) > 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_builtin_skill_graph_service_async_clustering() -> None:
    """Test async facade methods in BuiltinSkillGraphService."""
    registry = BuiltinSkillRegistryService()
    graph_service = BuiltinSkillGraphService(registry=registry)

    clusters = await graph_service.cluster_skills(min_cluster_size=2)
    assert len(clusters) >= 8
    assert "name" in clusters[0]
    assert "cluster_id" in clusters[0]

    caps = await graph_service.discover_emergent_capabilities()
    assert len(caps) >= 3
    assert "primary_skills" in caps[0]

    bridges = await graph_service.get_cross_cluster_bridges()
    assert len(bridges) > 0
    assert "source_cluster" in bridges[0]

    plan_dict = await graph_service.select_skills_for_task("audit codebase context files and prevent rot")
    assert "execution_pipeline" in plan_dict or "ordered_pipeline" in plan_dict
    pipeline = plan_dict.get("execution_pipeline") or plan_dict.get("ordered_pipeline")
    assert len(pipeline) > 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_skill_clustering_ioc_and_tools() -> None:
    """Test IoC service registration and tool mounting."""
    ctx = ServiceContext()
    tools = ToolRegistry()
    ctx.provide(TOOL_REGISTRY_KEY, tools)

    # 1. Test SkillRegistryPlugin registers SKILL_CLUSTERING_KEY
    reg_plugin = SkillRegistryPlugin()
    assert SKILL_CLUSTERING_KEY in reg_plugin.provides
    await reg_plugin.on_load(ctx)
    clustering_service = ctx.require(SKILL_CLUSTERING_KEY)
    assert isinstance(clustering_service, SkillClusteringService)

    # 2. Test SkillGraphPlugin mounts tools into ToolRegistry
    graph_plugin = SkillGraphPlugin()
    assert SKILL_CLUSTERING_KEY in graph_plugin.provides
    await graph_plugin.on_load(ctx)
    await graph_plugin.on_enable()

    mounted_tool_names = [t.name for t in tools.list_tools()]
    assert "select_skills" in mounted_tool_names
    assert "cluster_skills" in mounted_tool_names
    assert "discover_capabilities" in mounted_tool_names
    assert "get_skill_topology" in mounted_tool_names

    # 3. Test calling mounted select_skills tool
    tool_res = await tools.invoke("select_skills", {"task": "scaffold a deep agent skill with verification cards"})
    assert tool_res["status"] == "ok"
    payload = tool_res.get("result") or tool_res
    assert "plan" in payload
    assert len(payload["plan"]["execution_pipeline"]) > 0

    # 4. Test calling mounted cluster_skills tool
    c_res = await tools.invoke("cluster_skills", {"min_size": 2})
    assert c_res["status"] == "ok"
    c_payload = c_res.get("result") or c_res
    assert c_payload["total_clusters"] >= 8

    # 5. Test calling mounted discover_capabilities tool
    cap_res = await tools.invoke("discover_capabilities", {"query": "vault"})
    assert cap_res["status"] == "ok"
    cap_payload = cap_res.get("result") or cap_res
    assert cap_payload["total_capabilities"] > 0


@pytest.mark.unit
class TestSkillClusteringCLI:
    """Test Click CLI commands for clustering, emergent capabilities, and selection."""

    def test_cli_skills_select(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli_main, ["skills", "select", "modernize legacy codebase safely", "--max-skills", "3"])
        assert result.exit_code == 0
        assert "Intelligent Skill Selection Plan" in result.output
        assert "Topological Execution Pipeline" in result.output

    def test_cli_skills_clusters(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli_main, ["skills", "clusters", "--min-size", "2"])
        assert result.exit_code == 0
        assert "Discovered Skill Clusters" in result.output

    def test_cli_skills_capabilities(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli_main, ["skills", "capabilities"])
        assert result.exit_code == 0
        assert "Emergent Macro-Capabilities" in result.output


@pytest.mark.unit
def test_swarm_with_clustered_selection() -> None:
    """Test SwarmCoordinator automatically leverages select_skills_for_task."""
    ctx = ServiceContext()
    registry = BuiltinSkillRegistryService()
    ctx.provide(SKILL_REGISTRY_KEY, registry)

    coordinator = SwarmCoordinator(context=ctx)
    dag = coordinator.decompose_with_skills(
        "refactor legacy architecture seams and verify boundaries",
        include_verifier=True,
    )

    assert isinstance(dag, SwarmDAG)
    assert len(dag.nodes) >= 3

    # Check that tail verifier is connected to pipeline
    node_ids = list(dag.nodes.keys())
    assert any("verifier" in n for n in node_ids)
    last_node = dag.nodes[node_ids[-1]]
    assert len(last_node.dependencies) > 0


@pytest.mark.unit
def test_react_step_engine_skill_guidance_injection() -> None:
    """Test StepExecutionEngine automatically injects active skill guidance and gates into system prompt."""
    from unittest.mock import MagicMock

    from harness.agent.react import StepExecutionEngine

    ctx = ServiceContext()
    registry = BuiltinSkillRegistryService()
    ctx.provide(SKILL_CLUSTERING_KEY, registry)

    mock_llm = MagicMock()
    mock_tools = ToolRegistry()

    engine = StepExecutionEngine(llm=mock_llm, tools=mock_tools, context=ctx)
    messages = engine.build_initial_messages("modernize legacy codebase and map dependencies safely")

    system_msg = messages[0].content
    assert "Active Skill Knowledge Guidance" in system_msg
    assert "Recommended Pipeline:" in system_msg
    assert "Key Stage Gates:" in system_msg

