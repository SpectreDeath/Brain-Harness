"""Antigravity Trigger Runtime Entrypoints."""

from __future__ import annotations
from typing import Any


def register_interval_trigger(trigger_id: str, interval_seconds: float) -> dict[str, Any]:
    """Register an asynchronous interval wakeup trigger."""
    return {
        "trigger_id": trigger_id,
        "type": "interval",
        "interval_seconds": interval_seconds,
        "active": True,
    }


def register_file_change_trigger(trigger_id: str, file_path: str) -> dict[str, Any]:
    """Register a reactive file-change wakeup trigger."""
    return {
        "trigger_id": trigger_id,
        "type": "file_change",
        "file_path": file_path,
        "active": True,
    }


def fire_reactive_trigger(trigger_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Simulate reactive trigger wakeup."""
    return {
        "status": "fired",
        "trigger_id": trigger_id,
        "payload": payload,
    }
