"""Contract test suite for agentic-reliability-harness.

Verifies:
- Slotted and frozen domain dataclass immutability (Rule 12, Rule 43)
- Policy Enforcement Point (PEP) Gateway authorization boundaries
- Loop and non-progress detection (repetition and ping-pong oscillation)
- Independent Five-Level structural evaluation (Response, Step, Action, Workflow, System)
- Zero false success under fault invariant
- Three-state release gate decision logic (PASS, FAIL, INCONCLUSIVE)
- Statistical confidence intervals (Wilson lower bound and Rule of Three)
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
import pytest

# Ensure scripts dir is on sys.path
SKILL_ROOT = Path(__file__).resolve().parent.parent.parent / ".agents" / "skills" / "agentic-reliability-harness"
SCRIPTS_DIR = SKILL_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from arh_reliability_engine import (
    ControlExerciseKind,
    EvaluationLevel,
    EvaluationVerdict,
    ExecutionRecord,
    FaultDomain,
    FiveLevelEvaluatorEngine,
    GateDecision,
    GateScorecard,
    GatewayOutcome,
    LoopNonProgressDetector,
    PolicyEnforcementGateway,
    Scenario,
    ScenarioExpectation,
    SecurityContext,
    StepObservation,
    ThreeStateReleaseGate,
    ToolCall,
)
from arh_reliability_harness import (
    create_reference_support_scenario,
    format_scorecard_ascii,
    run_reference_workflow,
)


class TestAgenticReliabilityHarnessContract:
    """Test contract for the agentic reliability testing harness."""

    def test_slotted_frozen_dataclass_immutability(self) -> None:
        """Verify Rule 12 and Rule 43: Slotted & frozen dataclasses prevent mutation."""
        sec_ctx = SecurityContext(
            subject_id="sub_1",
            actor_id="actor_1",
            tenant_id="tenant_1",
            granted_scopes=("scope_a",),
        )
        # Direct attribute assignment must raise AttributeError/TypeError (Rule 43)
        with pytest.raises((AttributeError, TypeError)):
            sec_ctx.subject_id = "mutated"  # type: ignore

        tool_call = ToolCall(call_id="c1", tool_name="test_tool", arguments=(("k", "v"),))
        with pytest.raises((AttributeError, TypeError)):
            tool_call.tool_name = "other_tool"  # type: ignore

        verdict = EvaluationVerdict(
            level=EvaluationLevel.RESPONSE,
            status="pass",
            score=1.0,
            verdict_message="ok",
            evidence=(),
        )
        with pytest.raises((AttributeError, TypeError)):
            verdict.status = "fail"  # type: ignore

    def test_pep_gateway_authorization_and_identity_binding(self) -> None:
        """Verify PEP gateway enforces granted scopes and blocks unauthorized calls."""
        sec_ctx = SecurityContext(
            subject_id="sub_trusted",
            actor_id="agent_1",
            tenant_id="tenant_x",
            granted_scopes=("read:data",),
        )
        tools = {
            "read_info": lambda args: {"info": "safe"},
            "delete_info": lambda args: {"deleted": True},
        }
        scopes = {
            "read_info": {"read:data"},
            "delete_info": {"admin:delete"},
        }
        gateway = PolicyEnforcementGateway(
            security_context=sec_ctx,
            registered_tools=tools,
            tool_required_scopes=scopes,
        )

        # 1. Allowed call
        call_allowed = ToolCall(call_id="c1", tool_name="read_info", arguments=())
        outcome_allowed = gateway.execute(call_allowed)
        assert outcome_allowed.status == "executed"
        assert outcome_allowed.authorized is True
        assert outcome_allowed.result == {"info": "safe"}

        # 2. Denied call (missing admin:delete scope)
        call_denied = ToolCall(call_id="c2", tool_name="delete_info", arguments=())
        outcome_denied = gateway.execute(call_denied)
        assert outcome_denied.status == "rejected"
        assert outcome_denied.authorized is False
        assert "authorization_denied" in outcome_denied.reason

    def test_loop_non_progress_detector(self) -> None:
        """Verify action repetition and ping-pong oscillation detection."""
        detector = LoopNonProgressDetector(max_identical_actions=3, max_ping_pong_cycles=2)

        # Repetition loop: tool_a -> tool_a -> tool_a
        call_a = ToolCall(call_id="ca", tool_name="tool_a", arguments=())
        obs_repetition = [
            StepObservation(step_number=1, tool_call=call_a, gateway_outcome=None),
            StepObservation(step_number=2, tool_call=call_a, gateway_outcome=None),
            StepObservation(step_number=3, tool_call=call_a, gateway_outcome=None),
        ]
        has_loop, reason = detector.check_trajectory(obs_repetition)
        assert has_loop is True
        assert "repeated_tool_tool_a_times_3" in reason

        # Ping-pong oscillation: A -> B -> A -> B
        call_b = ToolCall(call_id="cb", tool_name="tool_b", arguments=())
        obs_pingpong = [
            StepObservation(step_number=1, tool_call=call_a, gateway_outcome=None),
            StepObservation(step_number=2, tool_call=call_b, gateway_outcome=None),
            StepObservation(step_number=3, tool_call=call_a, gateway_outcome=None),
            StepObservation(step_number=4, tool_call=call_b, gateway_outcome=None),
        ]
        detector_osc = LoopNonProgressDetector(max_ping_pong_cycles=1)
        has_osc, osc_reason = detector_osc.check_trajectory(obs_pingpong)
        assert has_osc is True
        assert "oscillation_detected" in osc_reason

    def test_five_level_evaluators_happy_path(self) -> None:
        """Verify all 5 structural levels pass on a healthy execution."""
        scenario = create_reference_support_scenario(expect_fault=False)
        record = run_reference_workflow(scenario, inject_incident_timeout=False)

        evaluator = FiveLevelEvaluatorEngine()
        verdicts = evaluator.evaluate(scenario, record)
        assert len(verdicts) == 5

        levels = {v.level: v for v in verdicts}
        assert levels[EvaluationLevel.RESPONSE].status == "pass"
        assert levels[EvaluationLevel.STEP].status == "pass"
        assert levels[EvaluationLevel.ACTION].status == "pass"
        assert levels[EvaluationLevel.WORKFLOW].status == "pass"
        assert levels[EvaluationLevel.SYSTEM].status == "pass"

    def test_zero_false_success_under_fault(self) -> None:
        """Verify injected faults are handled faithfully without false success."""
        scenario = create_reference_support_scenario(expect_fault=True)
        record = run_reference_workflow(scenario, inject_incident_timeout=True)

        evaluator = FiveLevelEvaluatorEngine()
        verdicts = evaluator.evaluate(scenario, record)
        levels = {v.level: v for v in verdicts}

        # The agent safely stopped without a ticket, which was an acceptable outcome
        assert levels[EvaluationLevel.WORKFLOW].status == "pass"
        assert record.world_state_dict["status"] == "safe_stop_no_ticket"
        assert len(record.faults_encountered) > 0

    def test_three_state_release_gate_logic(self) -> None:
        """Verify PASS, FAIL, and INCONCLUSIVE three-state gate logic."""
        gate = ThreeStateReleaseGate(min_trials=10, enforce_zero_false_success=True)

        verdict_pass = EvaluationVerdict(
            level=EvaluationLevel.WORKFLOW,
            status="pass",
            score=1.0,
            verdict_message="ok",
            evidence=(),
        )
        verdict_fail = EvaluationVerdict(
            level=EvaluationLevel.ACTION,
            status="fail",
            score=0.0,
            verdict_message="unauthorized",
            evidence=(),
        )

        # 1. PASS case: All pass, sufficient trials, 0 false success
        scorecard_pass = gate.evaluate_gate(
            verdicts=(verdict_pass,),
            total_trials=12,
            successful_trials=12,
            false_success_under_fault_count=0,
            unexercised_controls_count=0,
        )
        assert scorecard_pass.decision == GateDecision.PASS
        assert scorecard_pass.passed is True

        # 2. FAIL case: Has failure
        scorecard_fail = gate.evaluate_gate(
            verdicts=(verdict_pass, verdict_fail),
            total_trials=12,
            successful_trials=11,
            false_success_under_fault_count=0,
            unexercised_controls_count=0,
        )
        assert scorecard_fail.decision == GateDecision.FAIL
        assert scorecard_fail.passed is False

        # 3. FAIL case: False success under fault > 0
        scorecard_fault_fail = gate.evaluate_gate(
            verdicts=(verdict_pass,),
            total_trials=12,
            successful_trials=12,
            false_success_under_fault_count=1,
            unexercised_controls_count=0,
        )
        assert scorecard_fault_fail.decision == GateDecision.FAIL
        assert scorecard_fault_fail.passed is False

        # 4. INCONCLUSIVE case: Insufficient trials (e.g. 5 < 10)
        scorecard_inconclusive = gate.evaluate_gate(
            verdicts=(verdict_pass,),
            total_trials=5,
            successful_trials=5,
            false_success_under_fault_count=0,
            unexercised_controls_count=0,
        )
        assert scorecard_inconclusive.decision == GateDecision.INCONCLUSIVE
        assert scorecard_inconclusive.passed is False

    def test_statistical_confidence_bounds(self) -> None:
        """Verify Rule of Three and Wilson score bounds."""
        # Rule of Three: p <= 3 / n
        assert math.isclose(ThreeStateReleaseGate.calculate_rule_of_three(30), 0.10)
        assert math.isclose(ThreeStateReleaseGate.calculate_rule_of_three(100), 0.03)

        # Wilson Lower Bound: 10/10 successes at 95% CI should be >= 0.70
        lower = ThreeStateReleaseGate.calculate_wilson_lower_bound(10, 10)
        assert 0.70 <= lower <= 1.0

    def test_scorecard_ascii_formatting(self) -> None:
        """Verify ASCII scorecard output rendering."""
        scenario = create_reference_support_scenario()
        record = run_reference_workflow(scenario)
        evaluator = FiveLevelEvaluatorEngine()
        verdicts = evaluator.evaluate(scenario, record)
        gate = ThreeStateReleaseGate(min_trials=10)
        scorecard = gate.evaluate_gate(verdicts, 10, 10, 0, 0)

        ascii_card = format_scorecard_ascii(scorecard)
        assert "AGENTIC AI RELIABILITY SCORECARD" in ascii_card
        assert "PASS" in ascii_card
        assert "RESPONSE" in ascii_card
        assert "WORKFLOW" in ascii_card
