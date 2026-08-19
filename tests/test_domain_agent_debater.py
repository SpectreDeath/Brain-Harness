"""Tests for Domain 5: Agent Debater plugin."""

from __future__ import annotations

import pytest

from plugins.agent_orchestration.agent_debater.main import (
    conduct_dialectical_debate,
    synthesize_debate_verdict,
)


@pytest.mark.unit
class TestAgentDebaterPlugin:
    def test_conduct_dialectical_debate(self) -> None:
        pro = ["Micro-kernels reduce coupling", "Plugins can be sandboxed"]
        con = ["Micro-kernels have IPC overhead"]
        res = conduct_dialectical_debate("Adopt Micro-Kernel Architecture", pro, con)
        assert res["status"] == "ok"
        assert res["total_rounds"] == 2
        assert len(res["rounds"]) == 2
        assert res["rounds"][0]["proposer_claim"] == "Micro-kernels reduce coupling"

    def test_synthesize_debate_verdict(self) -> None:
        summary = {
            "topic": "Switch database to NoSQL",
            "rounds": [{"round_number": 1}],
            "pro_points_count": 1,
            "con_points_count": 3,
        }
        res = synthesize_debate_verdict(summary)
        assert res["status"] == "ok"
        assert res["recommendation"] == "REJECT_OR_RETHINK"
        assert "⚖️ Arbiter Verdict" in res["verdict_markdown"]
