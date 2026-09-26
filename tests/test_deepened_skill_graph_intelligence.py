"""Test suite for Deepened Skill Graph Intelligence and Runtime Interceptor Seams.

Verifies:
1. Slotted and frozen SkillExecutionGuidance dataclass immutability (Rule 12 & Rule 43).
2. SkillIntelligenceService protocol and single-call guidance compilation seam.
3. BuiltinSkillRegistryService action interception for AST calls and declared anti-patterns.
4. SkillClusteringEngine shared authoritative topology consumption (zero-duplication).
5. StepExecutionEngine runtime anti-pattern interception and in-flight self-repair observation.
6. SwarmCoordinator integration via SKILL_INTELLIGENCE_KEY.
"""

from __future__ import annotations

import pytest

from harness.agent.react import StepExecutionEngine
from harness.agent.swarm import SwarmCoordinator, SwarmDAG
from harness.kernel.context import ServiceContext
from harness.services.skill_clustering import (
    SkillCluster,
    SkillClusteringEngine,
)
from harness.services.skill_graph import (
    SKILL_INTELLIGENCE_KEY,
    SKILL_REGISTRY_KEY,
    AntiPatternGuard,
    BuiltinSkillRegistryService,
    SkillAntiPatternDefinition,
    SkillCardDefinition,
    SkillExecutionGuidance,
    SkillIntelligenceService,
    SkillRegistryPlugin,
)
from harness.services.tools import ToolRegistry, ToolSpec


@pytest.mark.unit
def test_skill_execution_guidance_frozen_dataclass() -> None:
    """Verify SkillExecutionGuidance is slotted, frozen, and validates structure."""
    guidance = SkillExecutionGuidance(
        task="Test task",
        selected_skills=("skill-a", "skill-b"),
        execution_pipeline=("skill-a", "skill-b"),
        stages=({"skill": "skill-a", "name": "Stage 1", "completion_gate": "Gate 1"},),
        active_anti_patterns=({"anti_pattern": "Speculative Abstraction", "skill": "skill-a"},),
        confidence=0.88,
    )

    assert guidance.task == "Test task"
    assert guidance.selected_skills == ("skill-a", "skill-b")
    assert guidance.execution_pipeline == ("skill-a", "skill-b")
    assert guidance.confidence == 0.88

    # Verify immutability (Rule 12 & Rule 43)
    with pytest.raises((AttributeError, TypeError)):
        guidance.task = "Modified Task"


@pytest.mark.unit
def test_registry_action_interception_ast_and_antipatterns() -> None:
    """Verify BuiltinSkillRegistryService intercepts blocked AST calls and active skill anti-patterns."""
    import time

    registry = BuiltinSkillRegistryService()
    test_skill = SkillCardDefinition(
        name="test-guarded-skill",
        category="security",
        target="Guarded Skill for Anti-Pattern Interception",
        anti_patterns=[
            SkillAntiPatternDefinition(
                name="Hardcoded Secret Exposure",
                symptom="Inline credentials or API keys committed in plain text",
                remedy="Use secure environment variables or vault references",
            )
        ],
    )
    registry._skills_cache["test-guarded-skill"] = test_skill
    registry._last_scan_time = time.time()

    # 1. Clean action must yield zero violations
    clean_violations = registry.intercept_action(
        action_name="write_file",
        action_input={"path": "safe.py", "content": "print('hello world')"},
        active_skills=["test-guarded-skill"],
    )
    assert len(clean_violations) == 0

    # 2. Blocked AST call (e.g. eval or exec) must be flagged
    ast_violations = registry.intercept_action(
        action_name="run_command",
        action_input={
            "command": "python script.py",
            "code": "```python\neval('2 + 2')\n```",
        },
        active_skills=["test-guarded-skill"],
    )
    assert len(ast_violations) >= 1
    assert any("eval" in v.anti_pattern for v in ast_violations)

    # 3. Direct blocked function name in arguments
    direct_ast_violations = registry.intercept_action(
        action_name="python_exec",
        action_input={"command": "__import__('os').system('id')"},
        active_skills=["test-guarded-skill"],
    )
    assert len(direct_ast_violations) >= 1

    # 4. Declared skill anti-pattern phrase match
    ap_violations = registry.intercept_action(
        action_name="propose_plan",
        action_input={
            "plan": "We will implement Hardcoded Secret Exposure in this module."
        },
        active_skills=["test-guarded-skill"],
    )
    assert len(ap_violations) >= 1
    assert ap_violations[0].anti_pattern == "Hardcoded Secret Exposure"
    assert ap_violations[0].skill_name == "test-guarded-skill"

    # 5. Formatted self-repair observation
    obs = AntiPatternGuard.format_self_repair_observation(ap_violations)
    assert obs["status"] == "error"
    assert obs["corrective_action_required"] is True
    assert "Hardcoded Secret Exposure" in obs["anti_pattern_violation"]


@pytest.mark.unit
def test_skill_intelligence_service_protocol_and_guidance() -> None:
    """Verify BuiltinSkillRegistryService implements SkillIntelligenceService and compiles guidance."""
    registry = BuiltinSkillRegistryService()
    registry.discover_all(".")

    assert isinstance(registry, SkillIntelligenceService)

    guidance = registry.compile_execution_guidance("Modernize legacy repository and map causal topology")
    assert isinstance(guidance, SkillExecutionGuidance)
    assert guidance.confidence > 0.0
    assert len(guidance.selected_skills) > 0
    assert len(guidance.execution_pipeline) > 0

    # Plugin registration check
    plugin = SkillRegistryPlugin()
    assert SKILL_INTELLIGENCE_KEY in plugin.provides
    ctx = ServiceContext()
    import asyncio
    asyncio.run(plugin.on_load(ctx))
    assert ctx.has(SKILL_INTELLIGENCE_KEY)
    assert ctx.require(SKILL_INTELLIGENCE_KEY) is plugin._registry


@pytest.mark.unit
def test_skill_clustering_engine_shared_registry_topology() -> None:
    """Verify SkillClusteringEngine consumes authoritative registry topology with zero duplicate graph build."""
    registry = BuiltinSkillRegistryService()
    registry.discover_all(".")
    assert len(registry.edges) > 0

    # Initialize clustering engine with authoritative registry
    engine = SkillClusteringEngine(registry=registry)
    assert engine._registry is registry

    clusters = engine.cluster_skills(min_cluster_size=2)
    assert len(clusters) >= 8
    for c in clusters:
        assert isinstance(c, SkillCluster)
        assert len(c.skills) >= 2


@pytest.mark.asyncio
async def test_step_execution_engine_active_anti_pattern_interception() -> None:
    """Verify StepExecutionEngine intercepts anti-patterns before tool execution and returns self-repair observation."""
    import time

    ctx = ServiceContext()
    tools = ToolRegistry()

    invoked_actions: list[str] = []

    async def mock_handler(command: str = "") -> dict[str, str]:
        invoked_actions.append(command)
        return {"status": "ok", "output": "success"}

    tools.register(ToolSpec.from_callable(mock_handler, name="bash"))

    registry = BuiltinSkillRegistryService()
    test_skill = SkillCardDefinition(
        name="test-security-skill",
        category="security",
        target="Security verification skill",
        anti_patterns=[
            SkillAntiPatternDefinition(
                name="Plaintext Secret Storage",
                symptom="Committing passwords in plaintext files",
                remedy="Store in encrypted vault",
            )
        ],
    )
    registry._skills_cache["test-security-skill"] = test_skill
    registry._last_scan_time = time.time()
    ctx.provide(SKILL_REGISTRY_KEY, registry)
    ctx.provide(SKILL_INTELLIGENCE_KEY, registry)

    engine = StepExecutionEngine(tools=tools, context=ctx)
    engine.active_skills = ["test-security-skill"]

    # 1. Clean execution passes through to tool
    clean_obs = await engine.execute_step(
        action_name="bash",
        action_input={"command": "git status"},
    )
    assert clean_obs["status"] == "ok"
    assert "git status" in invoked_actions

    # 2. Action violating anti-pattern is intercepted BEFORE tool invocation
    invoked_count_before = len(invoked_actions)
    bad_obs = await engine.execute_step(
        action_name="bash",
        action_input={"command": "We will implement Plaintext Secret Storage now"},
    )

    # Tool must NOT have been executed
    assert len(invoked_actions) == invoked_count_before
    # Returned observation must be an actionable self-repair error
    assert bad_obs["status"] == "error"
    assert bad_obs["corrective_action_required"] is True
    assert "Plaintext Secret Storage" in bad_obs["anti_pattern_violation"]

    # 3. Blocked AST call in tool argument is also intercepted
    ast_bad_obs = await engine.execute_step(
        action_name="bash",
        action_input={"command": "python -c 'eval(x)'"},
    )
    assert len(invoked_actions) == invoked_count_before
    assert ast_bad_obs["status"] == "error"
    assert ast_bad_obs["corrective_action_required"] is True


@pytest.mark.unit
def test_swarm_coordinator_skill_intelligence_integration() -> None:
    """Verify SwarmCoordinator leverages SKILL_INTELLIGENCE_KEY for single-call decomposition."""
    ctx = ServiceContext()
    registry = BuiltinSkillRegistryService()
    registry.discover_all(".")
    ctx.provide(SKILL_INTELLIGENCE_KEY, registry)
    ctx.provide(SKILL_REGISTRY_KEY, registry)

    coordinator = SwarmCoordinator(context=ctx)
    dag: SwarmDAG = coordinator.decompose_with_skills(
        objective="Modernize legacy repository and map causal topology",
        top_k=3,
    )
    assert len(dag.nodes) >= 1


@pytest.mark.unit
def test_antipattern_guard_unified_evaluate_action() -> None:
    """Verify AntiPatternGuard.evaluate_action consolidates argument extraction, AST scans, and phrase matches."""
    test_skill = SkillCardDefinition(
        name="test-security-skill",
        category="security",
        target="Security verification skill",
        anti_patterns=[
            SkillAntiPatternDefinition(
                name="Plaintext Secret Storage",
                symptom="Committing passwords in plaintext files",
                remedy="Store in encrypted vault",
            )
        ],
    )
    skills_map = {"test-security-skill": test_skill}

    # 1. Clean action produces no violations
    clean_violations = AntiPatternGuard.evaluate_action(
        action_name="write_file",
        action_input={"path": "safe.py", "content": "print('hello world')"},
        active_skills=["test-security-skill"],
        skill_lookup=skills_map.get,
    )
    assert len(clean_violations) == 0

    # 2. Blocked AST call in parameters is caught
    ast_violations = AntiPatternGuard.evaluate_action(
        action_name="run_command",
        action_input={"command": "python -c 'eval(2 + 2)'"},
        active_skills=["test-security-skill"],
        skill_lookup=skills_map.get,
    )
    assert len(ast_violations) >= 1
    assert any("eval" in v.anti_pattern for v in ast_violations)

    # 3. Active anti-pattern phrase match is caught
    ap_violations = AntiPatternGuard.evaluate_action(
        action_name="propose_plan",
        action_input={"plan": "We will implement Plaintext Secret Storage now."},
        active_skills=["test-security-skill"],
        skill_lookup=skills_map.get,
    )
    assert len(ap_violations) >= 1
    assert ap_violations[0].anti_pattern == "Plaintext Secret Storage"


@pytest.mark.unit
def test_skill_execution_guidance_self_rendering() -> None:
    """Verify SkillExecutionGuidance self-renders system prompt blocks and augments messages."""
    from harness.services.llm import LLMMessage

    guidance = SkillExecutionGuidance(
        task="Audit repository and verify architecture",
        selected_skills=("repo-reader", "deepen-architecture"),
        execution_pipeline=("repo-reader", "deepen-architecture", "adversarial-agent-verifier"),
        stages=(
            {"skill": "repo-reader", "name": "Ingest", "completion_gate": "Repo parsed"},
            {"skill": "deepen-architecture", "name": "Analyze", "completion_gate": "Seams mapped"},
        ),
        active_anti_patterns=(
            {"anti_pattern": "Speculative Abstraction", "skill": "deepen-architecture"},
        ),
        confidence=0.92,
    )

    assert guidance.should_inject is True

    block = guidance.format_system_prompt_block()
    assert "## Active Skill Knowledge Guidance" in block
    assert "repo-reader -> deepen-architecture -> adversarial-agent-verifier" in block
    assert "[repo-reader] Ingest: Repo parsed" in block
    assert "Speculative Abstraction (deepen-architecture)" in block

    # Verify message injection
    initial_msg = LLMMessage(role="system", content="You are an autonomous assistant.")
    augmented = guidance.inject_into_message(initial_msg)
    assert augmented.role == "system"
    assert "You are an autonomous assistant." in augmented.content
    assert "## Active Skill Knowledge Guidance" in augmented.content


@pytest.mark.unit
def test_plugin_skill_intelligence_service_completeness() -> None:
    """Verify SkillGraphPlugin directly satisfies SkillIntelligenceService protocol."""
    from plugins.memory_and_epistemics.skill_knowledge_graph.main import (
        SkillGraphPlugin,
        plugin,
    )

    assert isinstance(plugin, SkillGraphPlugin)
    assert hasattr(plugin, "compile_execution_guidance")
    assert hasattr(plugin, "intercept_action")

    guidance = plugin.compile_execution_guidance("Modernize legacy codebase")
    assert isinstance(guidance, SkillExecutionGuidance)

    violations = plugin.intercept_action(
        action_name="python_exec",
        action_input={"command": "eval('bad')"},
    )
    assert len(violations) >= 1


@pytest.mark.unit
def test_cli_skills_guidance_and_intercept() -> None:
    """Verify Click CLI commands for guidance compilation and action interception (Rule 10)."""
    import json

    from click.testing import CliRunner

    from harness.commands.skills import skills_group

    runner = CliRunner()

    # 1. Test guidance command (human readable)
    res_guidance = runner.invoke(skills_group, ["guidance", "Modernize legacy codebase and map topology"])
    assert res_guidance.exit_code == 0
    assert "Active Skill Knowledge Guidance Plan" in res_guidance.output
    assert "Recommended Pipeline:" in res_guidance.output

    # 2. Test guidance command (--json)
    res_guidance_json = runner.invoke(skills_group, ["guidance", "Modernize legacy codebase", "--json"])
    assert res_guidance_json.exit_code == 0
    payload = json.loads(res_guidance_json.output)
    assert payload["status"] == "ok"
    assert len(payload["execution_pipeline"]) > 0

    # 3. Test intercept command clean
    res_clean = runner.invoke(skills_group, ["intercept", "read_file", "-p", "path=safe.txt"])
    assert res_clean.exit_code == 0
    assert "✓ PASSED (Clean)" in res_clean.output

    # 4. Test intercept command violation with --json
    res_bad = runner.invoke(skills_group, ["intercept", "run_cmd", "-p", "command=eval('hack')", "--json"])
    assert res_bad.exit_code == 0
    bad_payload = json.loads(res_bad.output)
    assert bad_payload["status"] == "error"
    assert len(bad_payload["violations"]) >= 1

