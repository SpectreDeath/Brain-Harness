"""Tests for Domain 5: Trajectory Auditor plugin."""

from __future__ import annotations

import pytest

from plugins.security_and_forensics.trajectory_auditor.main import (
    audit_trajectory_steps,
    detect_repetitive_loop,
    synthesize_recovery_prompt,
)


@pytest.mark.unit
class TestTrajectoryAuditorPlugin:
    def test_audit_trajectory_steps_healthy(self) -> None:
        steps = [
            {"step_number": 1, "action": "fs_read_file", "observation": "file content"},
            {"step_number": 2, "action": "python_eval", "observation": "result 42"},
        ]
        res = audit_trajectory_steps(steps)
        assert res["status"] == "ok"
        assert res["healthy"] is True
        assert res["failed_steps_count"] == 0

    def test_detect_repetitive_loop(self) -> None:
        actions = ["search_text", "read_file", "search_text", "read_file"]
        res = detect_repetitive_loop(actions)
        assert res["has_loop"] is True
        assert "Oscillating loop detected" in str(res["pattern"])

    def test_synthesize_recovery_prompt(self) -> None:
        res = synthesize_recovery_prompt("Looping on same failing file read", last_failed_action="fs_read_file")
        assert res["status"] == "ok"
        assert "SYSTEM INTERVENTION" in res["recovery_prompt"]
        assert "Stop repeating 'fs_read_file'" in res["recovery_prompt"]
