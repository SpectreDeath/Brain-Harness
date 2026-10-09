"""Antigravity IDE protobuf enum mappings and stream codec entrypoint invariants."""

from __future__ import annotations

import sys

# UTF-8 stream codec entrypoint invariant (Rule 23, Rule 50)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Antigravity IDE Protobuf Enum Mappings
STATUS_MAP: dict[int, str] = {
    0: "UNSPECIFIED",
    1: "RUNNING",
    2: "IN_PROGRESS",
    3: "DONE",
    4: "PAUSED",
    5: "SKIPPED",
    6: "CANCELLED",
    7: "FAILED",
}

STEP_TYPE_MAP: dict[int, str] = {
    5: "USER_INPUT",
    7: "PLANNER_RESPONSE",
    8: "TOOL_EXECUTION",
    9: "TOOL_RESULT",
    14: "CONTEXT_UPDATE",
    15: "STREAM_CHUNK",
    17: "PLANNER_THOUGHT",
    21: "AGENT_INVOCATION",
    23: "SUBAGENT_RETURN",
    98: "TASK_STATUS",
    99: "SYSTEM_NOTIFICATION",
    101: "HOOK_EXECUTION",
    132: "BATTLE_MODE",
}

__all__ = [
    "STATUS_MAP",
    "STEP_TYPE_MAP",
]
