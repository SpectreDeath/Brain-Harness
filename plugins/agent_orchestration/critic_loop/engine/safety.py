"""Destructive shell command safety gatekeeping and pattern matching."""

from __future__ import annotations

import re
import sys
from typing import Any

from plugins.agent_orchestration.critic_loop.engine.models import _DANGEROUS_PATTERNS

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def check_command_safety(command: str) -> dict[str, Any]:
    """Scan shell commands for dangerous or irreversible operations."""
    cleaned = command.strip()
    violations: list[str] = []

    for pattern, description in _DANGEROUS_PATTERNS:
        if re.search(pattern, cleaned, flags=re.IGNORECASE):
            violations.append(description)

    is_safe = len(violations) == 0
    risk_level = "low"
    if violations:
        risk_level = (
            "critical"
            if any("destruction" in v or "removal" in v or "overwrite" in v for v in violations)
            else "high"
        )

    return {
        "status": "ok",
        "command": command,
        "is_safe": is_safe,
        "risk_level": risk_level,
        "violations_count": len(violations),
        "violations": violations,
    }


__all__ = ["check_command_safety"]
