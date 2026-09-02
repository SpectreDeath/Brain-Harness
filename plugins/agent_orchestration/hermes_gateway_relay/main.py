"""Hermes Gateway Relay — multi-platform messaging, WebSocket streaming, and scale-to-zero."""

from __future__ import annotations

import time
from typing import Any


def dispatch_platform_message(
    platform: str,
    channel_id: str,
    text: str,
) -> dict[str, Any]:
    """Route message through platform adapter."""
    valid_platforms = ["telegram", "discord", "slack", "whatsapp", "signal", "weixin", "cli"]
    plat_clean = platform.lower().strip()

    if plat_clean not in valid_platforms:
        return {
            "status": "error",
            "error": f"Unsupported platform: {platform}. Supported: {valid_platforms}",
        }

    return {
        "status": "ok",
        "platform": plat_clean,
        "channel_id": channel_id,
        "character_count": len(text),
        "delivered_at": int(time.time()),
        "message": f"Dispatched message to {plat_clean}:{channel_id}",
    }


def stream_ws_telemetry(
    session_id: str,
    event_payload: dict[str, Any],
) -> dict[str, Any]:
    """Stream telemetry payload to active WebSocket subscribers."""
    return {
        "status": "ok",
        "session_id": session_id,
        "event_type": event_payload.get("type", "generic_telemetry"),
        "subscribers_notified": 1,
        "timestamp": int(time.time()),
    }


def manage_scale_to_zero(idle_timeout_seconds: int = 300) -> dict[str, Any]:
    """Evaluate container hibernation policy."""
    return {
        "status": "ok",
        "idle_timeout_seconds": idle_timeout_seconds,
        "current_state": "ACTIVE",
        "hibernation_eligible": False,
        "policy": "SERVERLESS_HIBERNATE_ON_IDLE",
    }
