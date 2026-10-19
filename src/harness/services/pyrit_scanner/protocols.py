"""Protocols for PyRIT Red-Teaming Scanner Service (Rule 2)."""

from __future__ import annotations

import sys
from typing import Any, Protocol, runtime_checkable

from harness.services.pyrit_scanner.models import (
    AttackVector,
    RedTeamTarget,
    VulnerabilityScorecard,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


@runtime_checkable
class PyritScannerService(Protocol):
    """Authoritative protocol for GenAI red-teaming, adversarial probing, and scorecards."""

    async def scan_target(
        self, target: RedTeamTarget, vector: AttackVector
    ) -> VulnerabilityScorecard:
        """Execute adversarial evaluation scan against designated target."""
        ...

    async def generate_attack_plan(
        self, target: RedTeamTarget, vector: AttackVector
    ) -> list[dict[str, Any]]:
        """Generate sequenced adversarial payloads without execution."""
        ...

    def list_available_techniques(self) -> tuple[str, ...]:
        """Return all supported attack vectors."""
        ...

    def get_runtime_status(self) -> dict[str, Any]:
        """Return sandbox venv provisioning status and active isolation state."""
        ...
