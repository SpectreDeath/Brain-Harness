"""Tests for Domain 2: CI Pipeline plugin."""

from __future__ import annotations

import pytest

from plugins.ci_pipeline.main import (
    audit_action_pins,
    find_circular_job_dependencies,
    validate_github_actions_workflow,
)


@pytest.mark.unit
class TestCiPipelinePlugin:
    def test_validate_github_actions_workflow(self) -> None:
        workflow = (
            "name: CI\n"
            "on: [push]\n"
            "jobs:\n"
            "  build:\n"
            "    runs-on: ubuntu-latest\n"
        )
        res = validate_github_actions_workflow(workflow)
        assert res["status"] == "ok"
        assert res["valid"] is False  # Missing explicit permissions
        assert res["issues"][0]["rule"] == "MissingExplicitPermissions"

    def test_find_circular_job_dependencies(self) -> None:
        cyclic_jobs = {
            "test": {"needs": ["build"]},
            "build": {"needs": ["deploy"]},
            "deploy": {"needs": ["test"]},
        }
        res = find_circular_job_dependencies(cyclic_jobs)
        assert res["status"] == "ok"
        assert res["has_cycle"] is True
        assert len(res["cycle_path"]) >= 3

    def test_audit_action_pins(self) -> None:
        workflow = "steps:\n  - uses: actions/checkout@v3\n  - uses: actions/setup-python@v4\n"
        res = audit_action_pins(workflow)
        assert res["status"] == "ok"
        assert res["pinned_securely"] is False
        assert res["unpinned_count"] == 2
