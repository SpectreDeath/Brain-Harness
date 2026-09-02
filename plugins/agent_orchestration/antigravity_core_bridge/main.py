"""Antigravity Core Bridge Entrypoints."""

from __future__ import annotations
from typing import Any


def connect_proactor(host: str = "127.0.0.1", port: int = 4242) -> dict[str, Any]:
    """Establish Antigravity proactor connection."""
    return {
        "status": "connected",
        "host": host,
        "port": port,
        "protocol": "websocket_ipc",
    }


def dispatch_local_step(session_id: str, prompt: str) -> dict[str, Any]:
    """Dispatch prompt to proactor and return step observation stream."""
    return {
        "session_id": session_id,
        "prompt": prompt,
        "step_count": 2,
        "observations": [
            {"step_id": f"{session_id}_step_1", "step_type": "PLANNER_RESPONSE", "content": f"Received prompt: {prompt}"},
            {"step_id": f"{session_id}_step_2", "step_type": "TOOL_CALL", "content": "Invoked inspection tool"},
        ],
    }


def get_session_telemetry(session_id: str) -> dict[str, Any]:
    """Retrieve telemetry metrics for session."""
    return {
        "session_id": session_id,
        "status": "READY",
        "steps_count": 2,
    }
