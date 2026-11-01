"""Contract verification tests for TokenEconomizer skill and domain engine.

Enforces Rule 12 (slotted/frozen models), Rule 43 (frozen dataclass mutation assertions),
and behavioral contracts across micro-skills, tool pruning, loop guard, and ledgers.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

_SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from harness.services.token_economizer import (
    MicroSkillFact,
    TokenLedgerMetrics,
    ToolPrunePolicy,
    TrajectoryTrace,
    TurnGuardDecision,
)
from token_economizer_engine import TokenEconomizerEngine


class TestTokenEconomizerFrozenDataclasses:
    """Validate Rule 12 and Rule 43 immutability contracts."""

    def test_micro_skill_fact_immutability(self) -> None:
        fact = MicroSkillFact(
            key="test_fact",
            state="ACTIVE",
            confirms_count=3,
            contradicts_count=0,
            score=2.44,
            firing_rate=0.8,
        )
        assert fact.key == "test_fact"
        assert fact.state == "ACTIVE"

        # Rule 43: Direct attribute assignment inside pytest.raises
        with pytest.raises((AttributeError, TypeError)):
            fact.score = 5.0  # type: ignore[misc]

    def test_tool_prune_policy_immutability(self) -> None:
        policy = ToolPrunePolicy(
            status="ok",
            pruned_tools=("notebook", "browser"),
            protected_tools=("read_file", "edit_file"),
            estimated_tokens_saved=700,
        )
        assert len(policy.pruned_tools) == 2
        with pytest.raises((AttributeError, TypeError)):
            policy.estimated_tokens_saved = 0  # type: ignore[misc]

    def test_turn_guard_decision_immutability(self) -> None:
        decision = TurnGuardDecision(
            is_stuck=True,
            tier=1,
            action="nudge",
            reason="Heuristic conjunction met",
            stagnation_ratio=0.25,
            envelope_ratio=1.3,
        )
        assert decision.action == "nudge"
        with pytest.raises((AttributeError, TypeError)):
            decision.action = "abort"  # type: ignore[misc]

    def test_trajectory_trace_immutability(self) -> None:
        trace = TrajectoryTrace(
            session_id="sess_123",
            agent_type="claude_code",
            turns_count=15,
            tool_calls_count=12,
        )
        with pytest.raises((AttributeError, TypeError)):
            trace.turns_count = 20  # type: ignore[misc]

    def test_token_ledger_metrics_immutability(self) -> None:
        ledger = TokenLedgerMetrics(
            total_in_tokens=10000,
            total_out_tokens=2000,
            net_tokens_saved=3500,
            net_cost_saved_usd=0.0105,
            active_microskills_count=2,
            pruned_tools_count=3,
            loop_nudges_count=1,
            loop_aborts_count=0,
        )
        with pytest.raises((AttributeError, TypeError)):
            ledger.net_tokens_saved = 5000  # type: ignore[misc]


class TestMicroSkillsLifecycle:
    """Validate 3-state lifecycle, drift confirmation, and asymmetric contradiction."""

    def test_drifted_confirmation_promotion(self) -> None:
        engine = TokenEconomizerEngine(k_promote=3)

        # Confirmations on the same file do NOT satisfy drift promotion
        f1 = engine.record_micro_skill_observation("pytest_cmd", success=True, edited_files=["test_a.py"])
        assert f1.state == "CANDIDATE"

        f2 = engine.record_micro_skill_observation("pytest_cmd", success=True, edited_files=["test_a.py"])
        assert f2.state == "CANDIDATE"

        # Now confirm on distinct files
        f3 = engine.record_micro_skill_observation("pytest_cmd", success=True, edited_files=["test_b.py"])
        assert f3.state == "CANDIDATE"

        f4 = engine.record_micro_skill_observation("pytest_cmd", success=True, edited_files=["test_c.py"])
        # Now 3 distinct file sets -> Promoted to ACTIVE!
        assert f4.state == "ACTIVE"
        assert f4.confirms_count == 4

        # Active skills list should include it
        active = engine.get_active_micro_skills()
        assert any(item.key == "pytest_cmd" for item in active)

    def test_asymmetric_contradiction_eviction(self) -> None:
        engine = TokenEconomizerEngine(k_promote=3, lam=5.0)

        # Promote a fact
        engine.record_micro_skill_observation("build_rule", success=True, edited_files=["f1.py"])
        engine.record_micro_skill_observation("build_rule", success=True, edited_files=["f2.py"])
        promoted = engine.record_micro_skill_observation("build_rule", success=True, edited_files=["f3.py"])
        assert promoted.state == "ACTIVE"

        # Contradiction with lambda=5.0 severely penalizes score
        demoted = engine.record_micro_skill_observation("build_rule", success=False)
        assert demoted.state == "RETIRED"
        assert demoted.score < 0.0

    def test_high_stakes_hard_kill(self) -> None:
        engine = TokenEconomizerEngine(k_promote=2, hard_kill=True)
        engine.record_micro_skill_observation("secret_rule", success=True, edited_files=["f1.py"], is_high_stakes=True)
        promoted = engine.record_micro_skill_observation("secret_rule", success=True, edited_files=["f2.py"], is_high_stakes=True)
        assert promoted.state == "ACTIVE"

        # Single contradiction kills high-stakes immediately
        killed = engine.record_micro_skill_observation("secret_rule", success=False, is_high_stakes=True)
        assert killed.state == "RETIRED"


class TestToolPruningStage:
    """Validate empirical evidence pruning and protected work surfaces."""

    def test_evidence_pruning_with_protected_invariants(self) -> None:
        engine = TokenEconomizerEngine()

        loaded_tools = ["read_file", "edit_file", "run_command", "browser_navigate", "sql_query"]
        history = [
            {"read_file": 5, "edit_file": 3, "run_command": 2, "browser_navigate": 0, "sql_query": 0},
            {"read_file": 8, "edit_file": 4, "run_command": 1, "browser_navigate": 0, "sql_query": 0},
        ]

        policy = engine.evaluate_tool_pruning(
            loaded_tools=loaded_tools,
            session_tool_history=history,
            inapplicable_tools=["sql_query"],
            evidence_sessions_threshold=2,
        )

        assert policy.status == "ok"
        # browser_navigate (unused across 2 sessions) and sql_query (inapplicable) must be pruned
        assert "browser_navigate" in policy.pruned_tools
        assert "sql_query" in policy.pruned_tools

        # Core tools must NEVER be pruned
        assert "read_file" not in policy.pruned_tools
        assert "edit_file" not in policy.pruned_tools
        assert "run_command" not in policy.pruned_tools

        assert policy.estimated_tokens_saved == 2 * 350


class TestTurnGuardFailureIntervention:
    """Validate 3-tier failure-loop detection, mirroring nudges, and hard backstop."""

    def test_healthy_turns_stay_at_tier_0(self) -> None:
        engine = TokenEconomizerEngine()
        healthy_turns = [
            {"tool": "read_file", "status": "ok", "file": "main.py"},
            {"tool": "edit_file", "status": "ok", "file": "main.py"},
            {"tool": "run_command", "status": "ok", "result": "passed"},
        ]
        decision = engine.evaluate_turn_guard(healthy_turns, envelope_turn_p90=20)
        assert not decision.is_stuck
        assert decision.tier == 0
        assert decision.action == "continue"

    def test_heuristic_conjunction_triggers_nudge(self) -> None:
        engine = TokenEconomizerEngine()
        # Formulate a stuck trajectory: 25 turns, churn >= 4, errors >= 6, repeats >= 20%, past envelope
        stuck_turns = []
        for i in range(26):
            stuck_turns.append({
                "tool": "edit_file",
                "file": "server.py",
                "status": "error",
                "is_error": True,
                "error_message": "ImportError: cannot import name 'X'" if i % 2 == 0 else "SyntaxError: invalid syntax",
            })

        decision = engine.evaluate_turn_guard(stuck_turns, envelope_turn_p90=20, envelope_margin=1.25)
        assert decision.is_stuck
        assert decision.tier == 1
        assert decision.action == "nudge"
        assert decision.nudge_text is not None
        assert "LoopGuard Intervention" in decision.nudge_text

    def test_hard_backstop_forces_abort(self) -> None:
        engine = TokenEconomizerEngine()
        # 55 turns against envelope 20 (2.75x > 2.5x backstop)
        runaway_turns = [{"tool": "read_file", "status": "error"} for _ in range(55)]

        decision = engine.evaluate_turn_guard(runaway_turns, envelope_turn_p90=20)
        assert decision.is_stuck
        assert decision.tier == 2
        assert decision.action == "abort"
        assert "exceeded hard backstop" in decision.reason
