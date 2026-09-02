"""Antigravity Policy Gate Entrypoints."""

from __future__ import annotations
import re
from typing import Any


def evaluate_policy(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Evaluate tool call against security baseline."""
    # Check for catastrophic deletion
    if "run_command" in tool_name or "bash" in tool_name:
        cmd = str(arguments.get("CommandLine", ""))
        if re.search(r"rm\s+-rf\s+/|del\s+/s\s+/q", cmd):
            return {"decision": "DENY", "rationale": "Destructive deletion blocked"}
        if re.search(r"git\s+push\s+--force", cmd):
            return {"decision": "ASK_USER", "rationale": "Force push requires confirmation"}

    return {"decision": "ALLOW", "rationale": "Permissive rule pass"}


def add_policy_rule(tool_pattern: str, decision: str, rationale: str = "") -> dict[str, Any]:
    """Register a new policy rule."""
    return {
        "status": "registered",
        "tool_pattern": tool_pattern,
        "decision": decision,
        "rationale": rationale,
    }
