"""Hermes Cron Scheduler — natural language unattended automation and incident lifecycle."""

from __future__ import annotations

import hashlib
import time
from typing import Any

# In-memory mock storage for jobs and incidents
_JOBS_STORE: dict[str, dict[str, Any]] = {
    "job_daily_audit": {
        "job_id": "job_daily_audit",
        "schedule": "0 9 * * *",
        "prompt": "Audit codebase changes and compile daily executive summary",
        "target_channel": "telegram:operations",
        "status": "active",
        "created_at": 1756780000,
        "last_run": 1756866400,
    }
}

_BLUEPRINTS = {
    "bp_nightly_backup": {
        "id": "bp_nightly_backup",
        "title": "Nightly Git Checkpoint & Backup",
        "schedule": "0 2 * * *",
        "description": "Commits all dirty workspace changes and archives repository checkpoints.",
    },
    "bp_competitor_news": {
        "id": "bp_competitor_news",
        "title": "Daily Competitor & Market Monitor",
        "schedule": "0 8 * * 1-5",
        "description": "Scrapes and synthesizes market announcements and tech releases.",
    },
    "bp_weekly_dependency_audit": {
        "id": "bp_weekly_dependency_audit",
        "title": "Weekly Dependency Security & CVE Audit",
        "schedule": "0 10 * * 1",
        "description": "Audits pyproject.toml and lockfiles against known vulnerability databases.",
    },
}


def schedule_natural_cron(
    schedule_expr: str,
    prompt_action: str,
    target_channel: str,
) -> dict[str, Any]:
    """Register a new scheduled job with normalized cron expression."""
    job_hash = hashlib.sha256(f"{schedule_expr}:{prompt_action}".encode("utf-8")).hexdigest()[:8]
    job_id = f"job_{job_hash}"

    job_entry = {
        "job_id": job_id,
        "schedule": schedule_expr,
        "prompt": prompt_action,
        "target_channel": target_channel,
        "status": "active",
        "created_at": int(time.time()),
        "last_run": None,
    }
    _JOBS_STORE[job_id] = job_entry

    return {
        "status": "ok",
        "job_id": job_id,
        "schedule": schedule_expr,
        "target_channel": target_channel,
        "message": f"Successfully registered unattended cron job '{job_id}'",
    }


def list_cron_jobs(status_filter: str = "all") -> dict[str, Any]:
    """List registered cron jobs matching filter."""
    res = []
    for job in _JOBS_STORE.values():
        if status_filter == "all" or job.get("status") == status_filter:
            res.append(job)

    return {
        "status": "ok",
        "total_jobs": len(res),
        "status_filter": status_filter,
        "jobs": res,
    }


def inspect_cron_incidents(
    job_id: str,
    limit: int = 10,
) -> dict[str, Any]:
    """Inspect incident logs for scheduled automations."""
    incidents = [
        {
            "incident_id": "inc_001",
            "job_id": job_id if job_id != "all" else "job_daily_audit",
            "timestamp": int(time.time()) - 3600,
            "severity": "info",
            "event": "Execution completed with 0 errors.",
            "duration_seconds": 14.2,
        }
    ]

    return {
        "status": "ok",
        "job_id": job_id,
        "incident_count": len(incidents[:limit]),
        "incidents": incidents[:limit],
    }


def manage_blueprint_catalog(
    action: str,
    blueprint_id: str = "",
) -> dict[str, Any]:
    """Browse or instantiate pre-configured cron blueprints."""
    if action == "list":
        return {
            "status": "ok",
            "blueprints": list(_BLUEPRINTS.values()),
            "total_blueprints": len(_BLUEPRINTS),
        }

    if action == "inspect":
        bp = _BLUEPRINTS.get(blueprint_id)
        if not bp:
            return {"status": "error", "error": f"Blueprint not found: {blueprint_id}"}
        return {"status": "ok", "blueprint": bp}

    if action == "instantiate":
        bp = _BLUEPRINTS.get(blueprint_id)
        if not bp:
            return {"status": "error", "error": f"Blueprint not found: {blueprint_id}"}
        return schedule_natural_cron(bp["schedule"], bp["description"], "cli:default")

    return {"status": "error", "error": f"Unknown action: {action}"}
