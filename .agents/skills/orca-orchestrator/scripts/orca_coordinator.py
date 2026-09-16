# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "structlog",
# ]
# ///
"""Orca Coordinator CLI helper utility for managing supervised worker loops."""

from __future__ import annotations

from dataclasses import dataclass
import json
import sys
import time

# Reconfigure stdout/stderr to UTF-8 (Rule 23)
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


@dataclass(slots=True, frozen=True)
class CoordinatorStatus:
    """Status record of an active coordinator loop session (Rule 12)."""

    run_id: str
    active_dispatches: int
    settled_dispatches: int
    failed_dispatches: int
    is_settled: bool

    def __post_init__(self) -> None:
        assert self.run_id and len(self.run_id.strip()) > 0, "run_id must be non-empty"


def format_coordinator_summary(status: CoordinatorStatus) -> str:
    """Render a human-readable summary of the coordinator loop status."""
    verdict = "SETTLED" if status.is_settled else "ACTIVE"
    return (
        f"Coordinator [{status.run_id}] - {verdict}\n"
        f"Active: {status.active_dispatches} | "
        f"Settled: {status.settled_dispatches} | "
        f"Failed: {status.failed_dispatches}"
    )


if __name__ == "__main__":
    status = CoordinatorStatus(
        run_id="run-local-init",
        active_dispatches=0,
        settled_dispatches=0,
        failed_dispatches=0,
        is_settled=True,
    )
    print(format_coordinator_summary(status))
