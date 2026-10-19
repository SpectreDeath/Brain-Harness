"""Tool implementations for PyRIT Red-Teaming plugin."""

from __future__ import annotations

import sys
from typing import Any

import structlog

from harness.services.pyrit_scanner import (
    AttackVector,
    DefaultPyritScannerService,
    RedTeamTarget,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = structlog.get_logger("harness.plugins.pyrit_red_teaming")
_SERVICE = DefaultPyritScannerService()


async def redteam_fuzz_prompt(prompt: str, intensity: int = 3) -> dict[str, Any]:
    """Fuzz target prompt with adversarial mutations."""
    try:
        target = RedTeamTarget(target_type="system_prompt", endpoint="memory")
        vector = AttackVector(technique="encoding_fuzz", intensity=intensity)
        card = await _SERVICE.scan_target(target, vector)
        return {
            "status": "ok",
            "attack_success_rate": card.attack_success_rate,
            "risk_level": card.risk_level,
            "leaked_tokens": list(card.leaked_system_tokens),
            "recommendations": list(card.recommendations),
        }
    except Exception as e:
        logger.error("redteam_fuzz_prompt_failed", error=str(e))
        return {"status": "error", "error": str(e)}


async def redteam_jailbreak_audit(
    target_type: str = "agent_loop",
    technique: str = "crescendo",
) -> dict[str, Any]:
    """Execute multi-turn jailbreak evaluation."""
    try:
        target = RedTeamTarget(target_type=target_type, endpoint="local")
        vector = AttackVector(technique=technique, intensity=3)
        card = await _SERVICE.scan_target(target, vector)
        return {
            "status": "ok",
            "technique": technique,
            "attack_success_rate": card.attack_success_rate,
            "risk_level": card.risk_level,
            "bypassed_boundaries": list(card.bypassed_tool_boundaries),
            "recommendations": list(card.recommendations),
        }
    except Exception as e:
        logger.error("redteam_jailbreak_audit_failed", error=str(e))
        return {"status": "error", "error": str(e)}


async def redteam_tool_tampering_check(tool_name: str, payload: str) -> dict[str, Any]:
    """Check tool boundary resilience against output hijacking."""
    try:
        target = RedTeamTarget(target_type="tool_interface", endpoint=tool_name)
        vector = AttackVector(technique="tool_hijack", intensity=4)
        card = await _SERVICE.scan_target(target, vector)
        return {
            "status": "ok",
            "tool_name": tool_name,
            "attack_success_rate": card.attack_success_rate,
            "risk_level": card.risk_level,
            "bypassed_boundaries": list(card.bypassed_tool_boundaries),
        }
    except Exception as e:
        logger.error("redteam_tool_tampering_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def redteam_scorecard_report(session_id: str = "default") -> dict[str, Any]:
    """Return runtime isolation status and supported techniques."""
    status = _SERVICE.get_runtime_status()
    return {
        "status": "ok",
        "session_id": session_id,
        "runtime_status": status,
    }
