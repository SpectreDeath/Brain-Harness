"""Tests for Domain 5: Human in the Loop plugin."""

from __future__ import annotations

import pytest

from plugins.human_in_the_loop.main import (
    list_pending_approvals,
    record_human_decision,
    request_human_approval,
)


@pytest.mark.unit
class TestHumanInTheLoopPlugin:
    def test_request_and_record_approval(self) -> None:
        req = request_human_approval("DROP TABLE users;", risk_level="critical")
        assert req["status"] == "ok"
        req_id = req["request_id"]

        pending = list_pending_approvals()
        assert pending["pending_count"] >= 1

        decision = record_human_decision(req_id, approved=True, reason="Verified in migration plan")
        assert decision["status"] == "ok"
        assert decision["approved"] is True
        assert decision["final_status"] == "approved"
