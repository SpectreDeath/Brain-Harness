"""Tests for Domain: Hermes Cron Scheduler plugin."""

from __future__ import annotations

import pytest

from plugins.agent_orchestration.hermes_cron_scheduler.main import (
    schedule_natural_cron,
    list_cron_jobs,
    inspect_cron_incidents,
    manage_blueprint_catalog,
)


@pytest.mark.unit
class TestHermesCronScheduler:
    def test_schedule_natural_cron(self) -> None:
        res = schedule_natural_cron("0 12 * * *", "Run daily test harness", "telegram:alerts")
        assert res["status"] == "ok"
        assert "job_" in res["job_id"]
        assert res["schedule"] == "0 12 * * *"

    def test_list_cron_jobs(self) -> None:
        res = list_cron_jobs("active")
        assert res["status"] == "ok"
        assert res["total_jobs"] >= 1
        assert any(j["job_id"] == "job_daily_audit" for j in res["jobs"])

    def test_inspect_cron_incidents(self) -> None:
        res = inspect_cron_incidents("job_daily_audit", limit=5)
        assert res["status"] == "ok"
        assert res["incident_count"] == 1
        assert res["incidents"][0]["severity"] == "info"

    def test_manage_blueprint_catalog(self) -> None:
        list_res = manage_blueprint_catalog("list")
        assert list_res["status"] == "ok"
        assert list_res["total_blueprints"] >= 3

        inspect_res = manage_blueprint_catalog("inspect", "bp_nightly_backup")
        assert inspect_res["status"] == "ok"
        assert "Nightly Git Checkpoint" in inspect_res["blueprint"]["title"]
