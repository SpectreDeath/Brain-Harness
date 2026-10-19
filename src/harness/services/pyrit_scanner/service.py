"""Default implementation of PyritScannerService (Rule 2)."""

from __future__ import annotations

import sys
import time
from typing import Any

from harness.services.pyrit_scanner.models import (
    VALID_TECHNIQUES,
    AttackVector,
    RedTeamTarget,
    VulnerabilityScorecard,
)
from harness.services.pyrit_scanner.protocols import PyritScannerService
from harness.services.pyrit_scanner.runner import PyritSubprocessRunner

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class DefaultPyritScannerService(PyritScannerService):
    """GenAI red-teaming service orchestrating adversarial evaluations."""

    def __init__(self, runner: PyritSubprocessRunner | None = None) -> None:
        self.runner = runner or PyritSubprocessRunner()

    async def scan_target(
        self, target: RedTeamTarget, vector: AttackVector
    ) -> VulnerabilityScorecard:
        payload = {
            "target_type": target.target_type,
            "endpoint": target.endpoint,
            "max_turns": target.max_turns,
            "technique": vector.technique,
            "intensity": vector.intensity,
            "payload_count": vector.payload_count,
        }
        res = await self.runner.execute_probe(payload)
        return VulnerabilityScorecard(
            attack_success_rate=float(res.get("attack_success_rate", 0.0)),
            leaked_system_tokens=tuple(res.get("leaked_tokens", ())),
            bypassed_tool_boundaries=tuple(res.get("bypassed_boundaries", ())),
            risk_level=str(res.get("risk_level", "low")),
            recommendations=tuple(res.get("recommendations", ())),
            elapsed_ms=float(res.get("elapsed_ms", 0.0)),
        )

    async def generate_attack_plan(
        self, target: RedTeamTarget, vector: AttackVector
    ) -> list[dict[str, Any]]:
        plan = []
        for i in range(vector.payload_count):
            plan.append({
                "step": i + 1,
                "technique": vector.technique,
                "intensity": vector.intensity,
                "probe": f"ADVERSARIAL_PROBE_{vector.technique.upper()}_T{i+1}",
                "target_endpoint": target.endpoint,
            })
        return plan

    def list_available_techniques(self) -> tuple[str, ...]:
        return tuple(sorted(VALID_TECHNIQUES))

    def get_runtime_status(self) -> dict[str, Any]:
        return {
            "venv_provisioned": self.runner.is_venv_ready(),
            "venv_path": self.runner.venv_path,
            "timeout_seconds": self.runner.timeout_seconds,
            "supported_techniques": list(sorted(VALID_TECHNIQUES)),
        }
