"""Tests for Domain 5: Agent Supervisor plugin."""

from __future__ import annotations

import pytest

from plugins.agent_orchestration.agent_supervisor.main import (
    coordinate_swarm_tasks,
    tally_consensus_votes,
)


@pytest.mark.unit
class TestAgentSupervisorPlugin:
    def test_coordinate_swarm_tasks(self) -> None:
        agents = [
            {"id": "agent_alpha", "role": "researcher"},
            {"id": "agent_beta", "role": "coder"},
        ]
        res = coordinate_swarm_tasks("Build full-stack app", agents, max_total_tokens=20000)
        assert res["status"] == "ok"
        assert res["swarm_size"] == 2
        assert len(res["assignments"]) == 2
        assert res["assignments"][0]["allocated_tokens"] == 10000

    def test_tally_consensus_votes_approved(self) -> None:
        votes = [
            {"agent_id": "a1", "vote": "approve", "confidence": 0.9},
            {"agent_id": "a2", "vote": "approve", "confidence": 0.8},
            {"agent_id": "a3", "vote": "reject", "confidence": 0.5},
        ]
        res = tally_consensus_votes(votes, threshold=0.66)
        assert res["status"] == "ok"
        assert res["approvals"] == 2
        assert res["consensus_reached"] is True
        assert res["decision"] == "APPROVED"

    def test_tally_consensus_votes_rejected(self) -> None:
        votes = [
            {"agent_id": "a1", "vote": "reject", "confidence": 0.9},
            {"agent_id": "a2", "vote": "reject", "confidence": 0.8},
        ]
        res = tally_consensus_votes(votes, threshold=0.5)
        assert res["status"] == "ok"
        assert res["consensus_reached"] is False
        assert res["decision"] == "REJECTED"
