"""Unit and integration tests for the Deepened Skill Graphing Architecture.

Verifies:
1. O(1) edge deduplication via _edge_keys set keying.
2. Corrected DAG topology directionality (prerequisites vs downstream handoffs).
3. Authoritative factory seams (get_skill_registry, get_skill_graph) with IoC resolution.
4. Zero split-brain state between SkillKnowledgeGraph and BuiltinSkillRegistryService.
5. Invalidation synchronization and shared clustering engine memoization.
"""

from __future__ import annotations

import time

import pytest

from harness.commands.skills import get_skill_graph, get_skill_registry
from harness.kernel.context import ServiceContext
from harness.services.skill_graph import (
    SKILL_REGISTRY_KEY,
    BuiltinSkillGraphService,
    BuiltinSkillRegistryService,
    EdgeType,
    SkillCardDefinition,
    SkillTopologyReport,
    get_default_skill_registry,
)
from plugins.memory_and_epistemics.skill_knowledge_graph.graph import (
    SkillKnowledgeGraph,
)
from plugins.memory_and_epistemics.skill_knowledge_graph.main import (
    get_clustering_engine,
    index_skill_catalog,
    invalidate_skill_catalog,
)


@pytest.mark.unit
def test_edge_indexing_o1_deduplication() -> None:
    """Assert that _edge_keys provides O(1) duplicate rejection without expanding _edges."""
    registry = BuiltinSkillRegistryService()
    registry._skills_cache["skill-a"] = SkillCardDefinition(
        name="skill-a", category="test", target="Test Skill A"
    )
    registry._skills_cache["skill-b"] = SkillCardDefinition(
        name="skill-b", category="test", target="Test Skill B"
    )

    initial_edge_count = len(registry._edges)
    initial_key_count = len(registry._edge_keys)

    # Add new edge
    registry._add_edge("skill-a", "skill-b", EdgeType.REQUIRES)
    assert len(registry._edges) == initial_edge_count + 1
    assert len(registry._edge_keys) == initial_key_count + 1
    assert ("skill-a", "skill-b", EdgeType.REQUIRES) in registry._edge_keys

    # Attempt duplicate addition - must be a no-op
    registry._add_edge("skill-a", "skill-b", EdgeType.REQUIRES)
    assert len(registry._edges) == initial_edge_count + 1
    assert len(registry._edge_keys) == initial_key_count + 1


@pytest.mark.unit
def test_topology_directionality_prereqs_vs_downstream() -> None:
    """Verify strictly oriented DAG topology: prerequisites vs downstream handoffs."""
    registry = BuiltinSkillRegistryService()
    s_a = SkillCardDefinition(name="skill-a", category="test", target="Upstream Producer")
    s_b = SkillCardDefinition(
        name="skill-b", category="test", target="Consumer / Dependent", dependencies=["skill-a"]
    )
    s_c = SkillCardDefinition(name="skill-c", category="test", target="Pipeline Stage")

    registry._skills_cache["skill-a"] = s_a
    registry._skills_cache["skill-b"] = s_b
    registry._skills_cache["skill-c"] = s_c

    # skill-b REQUIRES skill-a (s_b -> s_a)
    registry._add_edge("skill-b", "skill-a", EdgeType.REQUIRES)
    # skill-a PRECEDES skill-c (s_a -> s_c)
    registry._add_edge("skill-a", "skill-c", EdgeType.PRECEDES)
    registry._last_scan_time = time.time()

    # 1. Topology of skill-b (the dependent)
    topo_b: SkillTopologyReport = registry.get_topology("skill-b")
    # skill-b requires skill-a, so skill-a MUST be in prerequisites
    assert "skill-a" in topo_b.prerequisites
    # skill-a is NOT a downstream handoff of skill-b
    assert "skill-a" not in topo_b.downstream_handoffs

    # 2. Topology of skill-a (the upstream dependency)
    topo_a: SkillTopologyReport = registry.get_topology("skill-a")
    # skill-b requires skill-a, so skill-b MUST be in downstream_handoffs for skill-a
    assert "skill-b" in topo_a.downstream_handoffs
    # skill-b must NOT be in prerequisites of skill-a
    assert "skill-b" not in topo_a.prerequisites

    # skill-a precedes skill-c, so skill-c MUST be in downstream_handoffs for skill-a
    assert "skill-c" in topo_a.downstream_handoffs

    # 3. Topology of skill-c
    topo_c: SkillTopologyReport = registry.get_topology("skill-c")
    # skill-a precedes skill-c, so skill-a MUST be in prerequisites of skill-c
    assert "skill-a" in topo_c.prerequisites
    assert "skill-a" not in topo_c.downstream_handoffs


@pytest.mark.unit
def test_get_skill_registry_seam_resolution() -> None:
    """Verify single-source factory seam resolution with and without IoC context."""
    # 1. Default process-scoped singleton resolution
    reg1 = get_skill_registry()
    reg2 = get_skill_registry()
    assert reg1 is reg2
    assert isinstance(reg1, BuiltinSkillRegistryService)

    # 2. Graph factory resolution
    graph1 = get_skill_graph()
    graph2 = get_skill_graph()
    assert graph1 is graph2
    assert isinstance(graph1, BuiltinSkillGraphService)

    # 3. IoC context override
    custom_reg = BuiltinSkillRegistryService(default_root=".")
    ctx = ServiceContext()
    ctx.provide(SKILL_REGISTRY_KEY, custom_reg)

    resolved = get_skill_registry(".", context=ctx)
    assert resolved is custom_reg
    assert resolved is not reg1


@pytest.mark.unit
def test_zero_split_brain_unification() -> None:
    """Assert SkillKnowledgeGraph acts as a zero-split-brain adapter over BuiltinSkillRegistryService."""
    custom_reg = BuiltinSkillRegistryService()
    custom_reg.discover_all(".")
    assert len(custom_reg._skills_cache) > 0

    # Adapt into SkillKnowledgeGraph
    skg = SkillKnowledgeGraph(registry=custom_reg)

    # Nodes, edges, and categories must match exactly
    assert skg.nodes is custom_reg._skills_cache
    assert skg.edges == custom_reg.edges
    assert skg.categories is custom_reg._categories

    # Dynamically adding a skill through the facade reflects immediately in the registry
    mock_skill = SkillCardDefinition(
        name="mock-deepened-skill",
        category="testing",
        target="Verify zero split-brain reflection",
    )
    skg.add_skill(mock_skill)

    assert "mock-deepened-skill" in custom_reg._skills_cache
    assert custom_reg.get_skill("mock-deepened-skill") is mock_skill
    assert ("mock-deepened-skill", "cat:testing", EdgeType.BELONGS_TO) in custom_reg._edge_keys

    # Topology through facade matches registry
    topo = skg.get_topology("mock-deepened-skill")
    assert topo.skill.name == "mock-deepened-skill"

    # Snapshot serialization succeeds
    snap = skg.get_snapshot()
    assert snap.total_skills == len(custom_reg._skills_cache)
    assert "mock-deepened-skill" in snap.nodes


@pytest.mark.unit
def test_plugin_and_registry_invalidation_synchronization() -> None:
    """Assert cache invalidation synchronizes across plugin and kernel registry."""
    index_skill_catalog(".")
    engine1 = get_clustering_engine()
    assert engine1 is not None

    # Invalidate catalog
    invalidate_skill_catalog()
    reg = get_default_skill_registry()
    assert reg._clustering_engine is None
    assert len(reg._skills_cache) == 0
    assert len(reg._edge_keys) == 0

    # Re-indexing re-populates both cleanly
    res = index_skill_catalog(".")
    assert res["status"] == "ok"
    assert res["total_nodes"] > 0
    assert len(reg._edge_keys) > 0


@pytest.mark.unit
def test_multi_tier_guidance_fallback_intent_and_bfs() -> None:
    """Assert compile_execution_guidance cascades from clustering to intent routing and BFS shortest path."""
    registry = BuiltinSkillRegistryService()
    s1 = SkillCardDefinition(
        name="alpha-scanner",
        category="testing",
        target="Scan source code files for anomalies",
        triggers=["alpha scan", "scan files"],
    )
    s2 = SkillCardDefinition(
        name="beta-analyzer",
        category="testing",
        target="Analyze scanned source code anomalies",
        triggers=["beta analyze", "analyze anomalies"],
        dependencies=["alpha-scanner"],
    )
    verifier = SkillCardDefinition(
        name="adversarial-agent-verifier",
        category="verification",
        target="Adversarial verification of results",
    )
    registry._skills_cache["alpha-scanner"] = s1
    registry._skills_cache["beta-analyzer"] = s2
    registry._skills_cache["adversarial-agent-verifier"] = verifier
    registry._add_edge("alpha-scanner", "beta-analyzer", EdgeType.PRECEDES)
    registry._last_scan_time = time.time()

    guidance = registry.compile_execution_guidance("alpha scan and analyze anomalies", max_skills=3)
    assert guidance is not None
    assert guidance.should_inject
    assert "alpha-scanner" in guidance.execution_pipeline
    assert "adversarial-agent-verifier" in guidance.execution_pipeline
    assert guidance.confidence > 0.20


@pytest.mark.unit
def test_invariant_aware_action_interception() -> None:
    """Assert AntiPatternGuard.evaluate_action evaluates mandatory skill invariants."""
    from harness.services.skill_graph import (
        AntiPatternGuard,
        SkillInvariantDefinition,
    )

    inv_skill = SkillCardDefinition(
        name="test-guarded-skill",
        category="engineering",
        target="Guarded skill with strict invariants",
        invariants=[
            SkillInvariantDefinition(
                rule="Artifact Metadata Restricted: The write_to_file tool only accepts ArtifactMetadata for files inside the conversation artifact directory.",
                is_blocking=True,
            ),
            SkillInvariantDefinition(
                rule="Scratch File Execution over Inline -c Strings: Never execute multi-line Python logic via python -c in commands.",
                is_blocking=True,
            ),
        ],
    )
    skills_map = {"test-guarded-skill": inv_skill}

    # 1. Action violating ArtifactMetadata on workspace file
    v_artifact = AntiPatternGuard.evaluate_action(
        action_name="write_to_file",
        action_input={"target_file": "d:/GitHub/projects/src/main.py", "ArtifactMetadata": {"Summary": "test"}},
        active_skills=["test-guarded-skill"],
        skill_lookup=skills_map.get,
    )
    assert len(v_artifact) >= 1
    assert any("Artifact Metadata" in getattr(v, "rule", "") or "Artifact Metadata" in getattr(v, "anti_pattern", "") for v in v_artifact)
    obs = AntiPatternGuard.format_self_repair_observation(v_artifact)
    assert obs["status"] == "error"
    assert "invariant_violation" in obs
    assert obs["corrective_action_required"] is True

    # 2. Action violating inline python -c execution
    v_cmd = AntiPatternGuard.evaluate_action(
        action_name="run_command",
        action_input={"CommandLine": 'python -c "import os; print(os.getcwd())"'},
        active_skills=["test-guarded-skill"],
        skill_lookup=skills_map.get,
    )
    assert len(v_cmd) >= 1
    assert any("Inline -c" in getattr(v, "rule", "") or "Inline -c" in getattr(v, "anti_pattern", "") for v in v_cmd)

    # 3. Clean action produces no violations
    v_clean = AntiPatternGuard.evaluate_action(
        action_name="view_file",
        action_input={"path": "src/main.py"},
        active_skills=["test-guarded-skill"],
        skill_lookup=skills_map.get,
    )
    assert len(v_clean) == 0


@pytest.mark.unit
def test_transitive_prerequisite_closure() -> None:
    """Assert get_prerequisite_closure computes full topological linear sequence."""
    registry = BuiltinSkillRegistryService()
    s_a = SkillCardDefinition(name="step-1", category="test", target="First step")
    s_b = SkillCardDefinition(name="step-2", category="test", target="Second step", dependencies=["step-1"])
    s_c = SkillCardDefinition(name="step-3", category="test", target="Third step", dependencies=["step-2"])

    registry._skills_cache["step-1"] = s_a
    registry._skills_cache["step-2"] = s_b
    registry._skills_cache["step-3"] = s_c

    registry._add_edge("step-2", "step-1", EdgeType.REQUIRES)
    registry._add_edge("step-3", "step-2", EdgeType.REQUIRES)
    registry._last_scan_time = time.time()

    closure_c = registry.get_prerequisite_closure("step-3")
    assert closure_c == ["step-1", "step-2"]

    closure_b = registry.get_prerequisite_closure("step-2")
    assert closure_b == ["step-1"]

    closure_a = registry.get_prerequisite_closure("step-1")
    assert closure_a == []


@pytest.mark.unit
def test_chain_feasibility_prerequisite_completeness_and_tools() -> None:
    """Assert evaluate_chain_feasibility catches missing prerequisites and missing tools."""
    from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry, ToolSpec

    registry = BuiltinSkillRegistryService()
    s_a = SkillCardDefinition(name="step-1", category="test", target="First step")
    s_b = SkillCardDefinition(name="step-2", category="test", target="Second step", dependencies=["step-1"], tools=["special_tool"])
    registry._skills_cache["step-1"] = s_a
    registry._skills_cache["step-2"] = s_b
    registry._add_edge("step-2", "step-1", EdgeType.REQUIRES)
    registry._last_scan_time = time.time()

    # 1. Missing prerequisite when verify_prerequisites=True
    feasible_1, missing_1 = registry.evaluate_chain_feasibility(["step-2"], verify_prerequisites=True)
    assert not feasible_1
    assert any("prerequisite_missing:step-2->step-1" in m for m in missing_1)

    # 2. Complete prerequisite chain without context passes
    feasible_2, missing_2 = registry.evaluate_chain_feasibility(["step-1", "step-2"], verify_prerequisites=True)
    assert feasible_2
    assert len(missing_2) == 0

    # 3. Context missing required tool
    ctx = ServiceContext()
    tools = ToolRegistry()
    ctx.provide(TOOL_REGISTRY_KEY, tools)
    feasible_3, missing_3 = registry.evaluate_chain_feasibility(["step-1", "step-2"], context=ctx)
    assert not feasible_3
    assert any("tool_missing:step-2:special_tool" in m for m in missing_3)

    # 4. Context with required tool registered passes
    tools.register(ToolSpec(name="special_tool", description="A special tool", executor=lambda: "ok"))
    feasible_4, missing_4 = registry.evaluate_chain_feasibility(["step-1", "step-2"], context=ctx)
    assert feasible_4
    assert len(missing_4) == 0


@pytest.mark.unit
def test_cache_invalidation_reentrancy_guard() -> None:
    """Assert BuiltinSkillRegistryService.invalidate_cache defends against recursive listener re-entrancy."""
    registry = BuiltinSkillRegistryService()
    call_count = 0

    def recursive_listener() -> None:
        nonlocal call_count
        call_count += 1
        registry.invalidate_cache()

    registry.add_invalidation_listener(recursive_listener)
    registry.invalidate_cache()

    assert call_count == 1


@pytest.mark.unit
def test_cli_prereqs_command() -> None:
    """Assert skills prereqs CLI command and programmatic seam work as expected."""
    from click.testing import CliRunner

    from harness.commands.skills import get_prerequisite_closure_cmd, skills_group

    res = get_prerequisite_closure_cmd("deepen-architecture")
    assert res["status"] == "ok"
    assert "prerequisites" in res
    assert "codebase-design" in res["prerequisites"]

    runner = CliRunner()
    cli_res = runner.invoke(skills_group, ["prereqs", "deepen-architecture"])
    assert cli_res.exit_code == 0
    assert "Transitive Prerequisite Closure" in cli_res.output
    assert "codebase-design" in cli_res.output


@pytest.mark.unit
def test_sync_export_html_brief() -> None:
    """Assert export_html_brief executes synchronously and generates valid brief."""
    from harness.commands.skills import export_skill_graph_visual_cmd

    reg = get_default_skill_registry()
    path = reg.export_html_brief()
    assert path.endswith(".html")

    cmd_res = export_skill_graph_visual_cmd()
    assert cmd_res["status"] == "ok"
    assert cmd_res["html_path"].endswith(".html")
