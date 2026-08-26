"""Ecosystem Bridge commands — pure async and synchronous entry points for bridge diagnostics."""

from __future__ import annotations

from typing import Any
from harness.bridges.locator import EcosystemLocator


def list_bridges_cmd() -> list[dict[str, Any]]:
    """Return discovery and capability status for all registered ecosystem bridges."""
    reports = EcosystemLocator.inspect_all()
    return [r.model_dump() for r in reports]


def check_bridge_status_cmd(project_name: str | None = None) -> dict[str, Any]:
    """Inspect status of a specific bridge or all bridges."""
    if project_name:
        report = EcosystemLocator.inspect_bridge(project_name)
        return {
            "status": "ok",
            "bridge": report.model_dump(),
        }

    reports = EcosystemLocator.inspect_all()
    connected_count = sum(1 for r in reports if r.available)
    return {
        "status": "ok",
        "total_bridges": len(reports),
        "connected_bridges": connected_count,
        "bridges": [r.model_dump() for r in reports],
    }
