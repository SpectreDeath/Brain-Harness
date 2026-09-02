"""Tests for Domain: Hermes Cognitive Engine plugin."""

from __future__ import annotations

import pytest

from plugins.agent_orchestration.hermes_cognitive_engine.main import (
    create_skill_from_trajectory,
    evaluate_verification_evidence,
    scrub_think_stream,
    nudge_learning_persistence,
)


@pytest.mark.unit
class TestHermesCognitiveEngine:
    def test_create_skill_from_trajectory(self) -> None:
        tools = ["read_file", "patch", "test_runner"]
        res = create_skill_from_trajectory("traj_123", "auto-debugger", "software-development", tools)
        assert res["status"] == "ok"
        assert res["skill_name"] == "auto-debugger"
        assert res["step_count"] == 3
        assert "Autonomously formed skill" in res["skill_markdown"]
        assert "Run `read_file`" in res["skill_markdown"]

    def test_evaluate_verification_evidence_pass(self) -> None:
        cmds = ["pytest tests/ -v"]
        mutations = ["src/module.py"]
        res = evaluate_verification_evidence("sess_001", cmds, mutations)
        assert res["status"] == "ok"
        assert res["verification_passed"] is True
        assert res["nudge_action"] == "PROCEED"

    def test_evaluate_verification_evidence_unverified_block(self) -> None:
        cmds = ["git status", "ls -la"]
        mutations = ["src/module.py"]
        res = evaluate_verification_evidence("sess_001", cmds, mutations)
        assert res["status"] == "warning"
        assert res["verification_passed"] is False
        assert res["nudge_action"] == "STOP_BLOCKED_UNVERIFIED_MUTATION"
        assert "Please run test suite" in res["message"]

    def test_scrub_think_stream(self) -> None:
        raw = "<think>Analyzing graph cycles...</think>Here is the clean solution."
        res = scrub_think_stream(raw, capture_telemetry=True)
        assert res["status"] == "ok"
        assert res["cleaned_text"] == "Here is the clean solution."
        assert res["thought_telemetry"] == "Analyzing graph cycles..."
        assert res["is_thinking"] is False

    def test_nudge_learning_persistence(self) -> None:
        res = nudge_learning_persistence(turn_count=10, complexity_score=0.9)
        assert res["status"] == "ok"
        assert res["should_nudge"] is True
        assert res["recommended_action"] == "PERSIST_KNOWLEDGE_ITEM"
