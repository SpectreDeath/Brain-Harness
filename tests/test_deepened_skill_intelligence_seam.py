"""Tests for the Deepened Skill Intelligence Seam, ActionGateResult, and resolve_skill_intelligence.

Verifies:
1. resolve_skill_intelligence context resolution precedence (Rule 1.1).
2. ActionGateResult slotted and frozen dataclass architecture (Rule 12, Rule 43).
3. evaluate_action_gate blocking and self-repair observation generation.
4. ReAct agent and Swarm coordinator single-seam delegation.
5. Encapsulated graph state accessors on BuiltinSkillRegistryService and SkillKnowledgeGraph facade.
6. Unified intent scoring delegation in SkillClusteringEngine.
"""

from __future__ import annotations

import pytest

from harness.kernel.context import ServiceContext
from harness.services.skill_graph import (
    SKILL_CLUSTERING_KEY,
    SKILL_INTELLIGENCE_KEY,
    SKILL_REGISTRY_KEY,
    ActionGateResult,
    BuiltinSkillRegistryService,
    SkillIntelligenceAdapter,
    SkillIntelligenceService,
    SkillRegistryService,
    resolve_skill_intelligence,
)


@pytest.mark.unit
def test_action_gate_result_slotted_frozen() -> None:
    """Verify ActionGateResult adheres to Rule 12 and Rule 43 (frozen dataclass immutability)."""
    res = ActionGateResult(
        action_name="run_command",
        is_blocked=True,
        violations=("v1",),
        observation={"status": "error", "reason": "blocked"},
    )

    assert res.action_name == "run_command"
    assert res.is_blocked is True
    assert res.violations == ("v1",)
    assert res.to_observation() == {"status": "error", "reason": "blocked"}

    # Rule 43: Immutability test using direct attribute assignment
    with pytest.raises((AttributeError, TypeError)):
        res.is_blocked = False  # type: ignore[misc]

    # Clean default observation test
    clean_res = ActionGateResult(action_name="read_file", is_blocked=False)
    assert clean_res.to_observation() == {"status": "ok"}


@pytest.mark.unit
def test_resolve_skill_intelligence_precedence() -> None:
    """Verify resolve_skill_intelligence resolves in strict precedence order (Rule 1.1)."""
    # 1. Empty / None context resolves to process singleton
    default_intel = resolve_skill_intelligence(None)
    assert isinstance(default_intel, BuiltinSkillRegistryService)

    # 2. Context with only SKILL_CLUSTERING_KEY
    ctx1 = ServiceContext()
    reg1 = BuiltinSkillRegistryService()
    ctx1.provide(SKILL_CLUSTERING_KEY, reg1)
    resolved1 = resolve_skill_intelligence(ctx1)
    assert resolved1 is reg1

    # 3. Context with SKILL_REGISTRY_KEY overrides clustering
    ctx2 = ServiceContext()
    reg2 = BuiltinSkillRegistryService()
    ctx2.provide(SKILL_CLUSTERING_KEY, reg1)
    ctx2.provide(SKILL_REGISTRY_KEY, reg2)
    resolved2 = resolve_skill_intelligence(ctx2)
    assert resolved2 is reg2

    # 4. Context with SKILL_INTELLIGENCE_KEY takes top precedence
    ctx3 = ServiceContext()
    reg3 = BuiltinSkillRegistryService()
    ctx3.provide(SKILL_CLUSTERING_KEY, reg1)
    ctx3.provide(SKILL_REGISTRY_KEY, reg2)
    ctx3.provide(SKILL_INTELLIGENCE_KEY, reg3)
    resolved3 = resolve_skill_intelligence(ctx3)
    assert resolved3 is reg3


@pytest.mark.unit
def test_evaluate_action_gate_clean_and_blocked() -> None:
    """Verify evaluate_action_gate correctly evaluates tool calls and arguments."""
    registry = BuiltinSkillRegistryService()

    # Clean action
    clean_gate = registry.evaluate_action_gate(
        action_name="read_file",
        action_input={"path": "src/harness/main.py"},
    )
    assert isinstance(clean_gate, ActionGateResult)
    assert clean_gate.is_blocked is False
    assert clean_gate.to_observation() == {"status": "ok"}

    # Blocked action with AST eval call in input
    blocked_gate = registry.evaluate_action_gate(
        action_name="run_command",
        action_input={"command": "python -c 'eval(\"2 + 2\")'"},
    )
    assert blocked_gate.is_blocked is True
    assert len(blocked_gate.violations) > 0
    obs = blocked_gate.to_observation()
    assert obs["status"] == "error"
    assert obs.get("corrective_action_required") is True


@pytest.mark.unit
def test_builtin_registry_state_accessors() -> None:
    """Verify public state accessors on BuiltinSkillRegistryService (encapsulation preservation)."""
    registry = BuiltinSkillRegistryService()
    registry.discover_all(".")

    nodes = registry.get_nodes()
    assert isinstance(nodes, dict)
    assert len(nodes) > 0

    cats = registry.get_categories()
    assert isinstance(cats, set)
    assert len(cats) > 0

    # Test edge accessors
    if "codebase-design" in nodes:
        out_edges = registry.get_outgoing_edges("codebase-design")
        assert isinstance(out_edges, list)

        in_edges = registry.get_incoming_edges("deepen-architecture")
        assert isinstance(in_edges, list)


@pytest.mark.unit
def test_plugin_facade_encapsulated_accessors() -> None:
    """Verify SkillKnowledgeGraph plugin facade delegates cleanly via public accessors."""
    from plugins.memory_and_epistemics.skill_knowledge_graph.graph import (
        SkillKnowledgeGraph,
    )

    registry = BuiltinSkillRegistryService()
    registry.discover_all(".")
    graph = SkillKnowledgeGraph(registry=registry)

    nodes = graph.get_nodes()
    assert isinstance(nodes, dict)
    assert len(nodes) == len(registry.get_nodes())

    cats = graph.get_categories()
    assert isinstance(cats, set)
    assert len(cats) == len(registry.get_categories())


@pytest.mark.unit
def test_clustering_engine_scoring_delegation() -> None:
    """Verify SkillClusteringEngine delegates skill scoring to route_intent when registry is attached."""
    registry = BuiltinSkillRegistryService()
    registry.discover_all(".")
    engine = registry._get_clustering_engine()

    plan = engine.select_skills_for_task(
        "run architecture deepening on codebase design seams",
        max_skills=4,
        include_verifier=True,
    )
    assert plan.task == "run architecture deepening on codebase design seams"
    assert len(plan.selected_skills) > 0
    # Should include deepened skill or codebase-design
    assert any("deepen" in s or "codebase" in s for s in plan.selected_skills)
    assert len(plan.execution_pipeline) > 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_react_step_execution_engine_single_seam_gating() -> None:
    """Verify StepExecutionEngine intercepts dangerous actions using the deepened evaluate_action_gate seam."""
    from harness.agent.react import StepExecutionEngine
    from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry

    ctx = ServiceContext()
    tools = ToolRegistry()
    ctx.provide(TOOL_REGISTRY_KEY, tools)

    engine = StepExecutionEngine(context=ctx, tools=tools)

    # Invoke tool safely with blocked call: eval
    obs = await engine._invoke_tool_safely(
        action_name="run_command",
        action_input={"command": "eval('import os; os.system(\"calc\")')"},
    )

    assert isinstance(obs, dict)
    assert obs.get("status") == "error"
    assert obs.get("corrective_action_required") is True


@pytest.mark.unit
def test_swarm_coordinator_single_seam_decomposition() -> None:
    """Verify SwarmCoordinator decomposes task objectives using the deepened single intelligence seam."""
    from harness.agent.swarm import SwarmCoordinator, SwarmDAG

    ctx = ServiceContext()
    coord = SwarmCoordinator(context=ctx)

    dag = coord.decompose_with_skills(
        "analyze and deepen codebase design architecture",
        top_k=3,
        include_verifier=True,
    )

    assert isinstance(dag, SwarmDAG)
    assert len(dag.nodes) > 0


@pytest.mark.unit
def test_resolve_skill_intelligence_adapts_partial_registry() -> None:
    """Verify resolve_skill_intelligence adapts partial / mock SkillRegistryService instances."""
    from unittest.mock import MagicMock

    ctx = ServiceContext()
    mock_reg = MagicMock(spec=SkillRegistryService)
    mock_reg.route_intent.return_value = {
        "status": "ok",
        "matches": [{"skill_name": "crafting-skills"}],
    }

    ctx.provide(SKILL_REGISTRY_KEY, mock_reg)
    resolved = resolve_skill_intelligence(ctx)

    assert isinstance(resolved, SkillIntelligenceAdapter)
    assert isinstance(resolved, SkillIntelligenceService)

    # Verify delegation
    res = resolved.route_intent("crafting-skills")
    assert res["status"] == "ok"
    assert res["matches"][0]["skill_name"] == "crafting-skills"
    mock_reg.route_intent.assert_called_once_with("crafting-skills", top_k=3)
