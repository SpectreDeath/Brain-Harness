"""Comprehensive unit tests for the deepened ai-agent-engineer tooling seams."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest
import yaml

# Add skill scripts directory to sys.path
SKILL_DIR = Path(__file__).parent.parent / ".agents" / "skills" / "ai-agent-engineer"
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from ladder_evaluator import LadderEvaluator, TaskScopingInput, LadderEvaluationResult
from capability_profiler import CapabilityProfiler, CapabilityProfile, ProfileValidationReport
from dynamic_model_router import DynamicModelRouter, ComplexityScore, RoutingDecision, ExecutionFallbackResult


@pytest.mark.unit
class TestLadderEvaluator:
    """Unit tests for the 4-Level Ladder & Pre-Flight Scoping Engine."""

    def test_level_1_classification_single_prompt(self) -> None:
        task = TaskScopingInput(
            task_description="Translate English text to German with formal tone",
            candidate_tools=[],
            estimated_steps=1,
            state_dependent_decisions=False,
            is_flow_invariant=True,
        )
        result = LadderEvaluator.evaluate(task)
        assert result.recommended_level == 1
        assert result.approved_for_implementation is True
        assert "Level 1" in result.level_name

    def test_level_2_classification_deterministic_workflow(self) -> None:
        task = TaskScopingInput(
            task_description="Run ETL: fetch data, clean schema, insert to database",
            candidate_tools=["fetch_api", "clean_schema", "db_insert"],
            estimated_steps=3,
            state_dependent_decisions=False,
            is_flow_invariant=True,
        )
        result = LadderEvaluator.evaluate(task)
        assert result.recommended_level == 2
        assert result.approved_for_implementation is True
        assert "Level 2" in result.level_name

    def test_level_3_bounded_agent_valid_scoping(self) -> None:
        task = TaskScopingInput(
            task_description="Triage support tickets, query database, update status",
            candidate_tools=["lookup_customer", "search_kb", "update_ticket"],
            estimated_steps=6,
            state_dependent_decisions=True,
            is_flow_invariant=False,
            success_metric=">= 90% resolution rate on day one without escalation",
            worst_case_blast_radius="Bounded to sandbox DB; no email dispatches to users",
            cost_ceiling_per_session=0.20,
            evaluation_harness_description="50 historical labeled session replay cases",
            off_switch_description="Instant SIGINT interrupt with transactional rollback in < 200ms",
        )
        result = LadderEvaluator.evaluate(task)
        assert result.recommended_level == 3
        assert result.all_questions_passed is True
        assert result.approved_for_implementation is True

    def test_level_3_bounded_agent_fails_on_vague_metrics(self) -> None:
        task = TaskScopingInput(
            task_description="Customer ticket assistant",
            candidate_tools=["lookup_customer", "update_ticket"],
            estimated_steps=5,
            state_dependent_decisions=True,
            success_metric="Users should really like it",  # Unquantified!
            worst_case_blast_radius="",  # Empty!
            cost_ceiling_per_session=0.0,  # Zero!
            evaluation_harness_description="We will figure this out later",  # Deferred!
            off_switch_description="",  # Missing!
        )
        result = LadderEvaluator.evaluate(task)
        assert result.recommended_level == 3
        assert result.all_questions_passed is False
        assert result.approved_for_implementation is False

    def test_level_4_escalation_long_horizon(self) -> None:
        task = TaskScopingInput(
            task_description="Autonomous repository refactoring and dependency modernization",
            candidate_tools=["git_cli", "ast_parser", "pytest_runner", "dependency_resolver"],
            estimated_steps=35,
            state_dependent_decisions=True,
            success_metric="100% test suite pass rate across 50 migration runs",
            worst_case_blast_radius="Isolated git branch; no remote push permissions",
            cost_ceiling_per_session=5.00,
            evaluation_harness_description="20 benchmark repository refactoring trajectories",
            off_switch_description="Sub-second process kill signal with git reset --hard rollback",
        )
        result = LadderEvaluator.evaluate(task)
        assert result.recommended_level == 4
        assert result.approved_for_implementation is True


@pytest.mark.unit
class TestCapabilityProfiler:
    """Unit tests for the 60 Canonical Patterns Capability Profiler."""

    def test_catalog_integrity(self) -> None:
        assert len(CapabilityProfiler.PATTERNS_CATALOG) == 60
        capabilities = {p.capability for p in CapabilityProfiler.PATTERNS_CATALOG.values()}
        assert capabilities == {
            "Perception", "Reasoning", "Planning", "Memory",
            "Tool Use", "Coordination", "Learning", "Alignment"
        }

    def test_valid_profile_passes(self) -> None:
        profile = CapabilityProfile(
            agent_name="clean_agent",
            target_level=3,
            declared_patterns=[17, 25, 30, 37, 53, 60],
            tools_count=6,
            has_external_mutations=True,
            estimated_session_steps=10,
        )
        report = CapabilityProfiler.validate_profile(profile)
        assert report.valid is True
        assert report.capability_counts["Planning"] >= 1
        assert report.capability_counts["Alignment"] >= 2

    def test_tool_sprawl_without_selector_fails(self) -> None:
        profile = CapabilityProfile(
            agent_name="bloated_agent",
            target_level=3,
            declared_patterns=[17, 25],  # Missing Pat 30 (Tool Selector)
            tools_count=22,  # > 15 tools!
            has_external_mutations=False,
            estimated_session_steps=5,
        )
        report = CapabilityProfiler.validate_profile(profile)
        assert report.valid is False
        error_rules = [f.rule_name for f in report.findings if f.severity == "ERROR"]
        assert "ToolSprawlSelector" in error_rules

    def test_consequential_mutation_without_constitution_fails(self) -> None:
        profile = CapabilityProfile(
            agent_name="reckless_agent",
            target_level=3,
            declared_patterns=[17, 30],  # Missing Pat 53 (Constitution) & Pat 37 (Auditor)
            tools_count=5,
            has_external_mutations=True,  # Performs mutations!
            estimated_session_steps=5,
        )
        report = CapabilityProfiler.validate_profile(profile)
        assert report.valid is False
        error_rules = [f.rule_name for f in report.findings if f.severity == "ERROR"]
        assert "ConsequentialMutationGuard" in error_rules

    def test_level_4_without_off_switch_fails(self) -> None:
        profile = CapabilityProfile(
            agent_name="rogue_agent",
            target_level=4,  # Full Agent!
            declared_patterns=[16, 17, 25, 37, 53],  # Missing Pat 60 (Off-Switch)!
            tools_count=8,
            has_external_mutations=True,
            estimated_session_steps=30,
        )
        report = CapabilityProfiler.validate_profile(profile)
        assert report.valid is False
        error_rules = [f.rule_name for f in report.findings if f.severity == "ERROR"]
        assert "OffSwitchMandatory" in error_rules


@pytest.mark.unit
class TestDynamicModelRouter:
    """Unit tests for the 3-Tier Dynamic Model Routing Engine."""

    def test_tier_1_complexity_analysis_low(self) -> None:
        prompt = "Summarize the customer request in 2 sentences"
        score = DynamicModelRouter.analyze_complexity(prompt, candidate_tools=[])
        assert score.tier == "LOW"
        assert score.reasoning_depth_detected is False

    def test_tier_1_complexity_analysis_high(self) -> None:
        prompt = "Formulate a formal invariant proof and deduce architectural causality for this failure"
        score = DynamicModelRouter.analyze_complexity(prompt, candidate_tools=["ast_tool", "solver_tool", "git_tool"])
        assert score.tier == "HIGH"
        assert score.reasoning_depth_detected is True

    def test_tier_2_routing_matrix_assignment(self) -> None:
        low_score = ComplexityScore(tier="LOW", complexity_score=0.1, token_count=100, reasoning_depth_detected=False, tool_interaction_count=0, intent_tag="test")
        high_score = ComplexityScore(tier="HIGH", complexity_score=0.8, token_count=3000, reasoning_depth_detected=True, tool_interaction_count=5, intent_tag="test")

        low_decision = DynamicModelRouter.route_model(low_score)
        assert "flash" in low_decision.primary_model or "haiku" in low_decision.primary_model
        assert low_decision.reasoning_budget == "OFF"

        high_decision = DynamicModelRouter.route_model(high_score)
        assert "thinking" in high_decision.primary_model or "sonnet" in high_decision.primary_model
        assert high_decision.reasoning_budget == "HIGH"

    def test_tier_3_fallback_chain_success_primary(self) -> None:
        decision = RoutingDecision(
            assigned_tier="MEDIUM",
            primary_model="claude-3-7-sonnet",
            fallback_chain=["gemini-2.5-flash", "gpt-4o"],
            estimated_cost_per_1k_tokens=0.003,
            reasoning_budget="LOW",
        )
        res = DynamicModelRouter.simulate_fallback_chain(decision, failing_providers=set())
        assert res.status == "SUCCESS"
        assert res.successful_model == "claude-3-7-sonnet"
        assert res.fallback_triggered is False
        assert res.attempts == 1

    def test_tier_3_fallback_chain_rollover_on_primary_outage(self) -> None:
        decision = RoutingDecision(
            assigned_tier="MEDIUM",
            primary_model="claude-3-7-sonnet",
            fallback_chain=["gemini-2.5-flash", "gpt-4o"],
            estimated_cost_per_1k_tokens=0.003,
            reasoning_budget="LOW",
        )
        # Primary provider has an outage
        res = DynamicModelRouter.simulate_fallback_chain(
            decision, failing_providers={"claude-3-7-sonnet"}
        )
        assert res.status == "SUCCESS"
        assert res.successful_model == "gemini-2.5-flash"
        assert res.fallback_triggered is True
        assert res.attempts == 2


@pytest.mark.unit
class TestConfigFileIntegrity:
    """Verify config.default.yaml loads cleanly and contains required keys."""

    def test_config_yaml_schema(self) -> None:
        config_path = SKILL_DIR / "config.default.yaml"
        assert config_path.exists(), "config.default.yaml does not exist"
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))

        assert "ladder" in data
        assert data["ladder"]["level_3_max_steps"] == 20
        assert data["ladder"]["level_4_max_steps"] == 40

        assert "tools" in data
        assert data["tools"]["max_tools_without_selector"] == 15
        assert data["tools"]["require_constitution_for_mutations"] is True

        assert "memory" in data
        assert data["memory"]["max_context_window_fraction"] == 0.60

        assert "model_routing" in data
        assert "tier_1_complexity_analysis" in data["model_routing"]
        assert "tier_2_model_matrix" in data["model_routing"]
        assert "tier_3_fallbacks" in data["model_routing"]
