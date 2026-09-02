"""Antigravity OTel Telemetry Entrypoints."""

from __future__ import annotations
import time
from typing import Any


def start_telemetry_span(name: str, span_id: str, parent_id: str = "") -> dict[str, Any]:
    """Start a new hierarchical telemetry span."""
    return {
        "span_id": span_id,
        "name": name,
        "parent_span_id": parent_id if parent_id else None,
        "start_time": time.time(),
        "status": "RECORDING",
    }


def end_telemetry_span(span_id: str, status: str = "OK") -> dict[str, Any]:
    """Close an active telemetry span."""
    return {
        "span_id": span_id,
        "end_time": time.time(),
        "status": status,
    }


def get_statusline_payload(mode: str = "idle") -> dict[str, Any]:
    """Generate Antigravity dynamic statusline IPC payload."""
    return {
        "mode": mode,
        "tokens": {
            "prompt": 1200,
            "completion": 350,
            "total": 1550,
            "context_fill_ratio": 0.0015,
        },
        "active_spans_count": 0,
        "completed_spans_count": 1,
    }
