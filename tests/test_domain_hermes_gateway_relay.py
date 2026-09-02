"""Tests for Domain: Hermes Gateway Relay plugin."""

from __future__ import annotations

import pytest

from plugins.agent_orchestration.hermes_gateway_relay.main import (
    dispatch_platform_message,
    stream_ws_telemetry,
    manage_scale_to_zero,
)


@pytest.mark.unit
class TestHermesGatewayRelay:
    def test_dispatch_platform_message_valid(self) -> None:
        res = dispatch_platform_message("telegram", "chat_456", "Hello from Brain Harness!")
        assert res["status"] == "ok"
        assert res["platform"] == "telegram"
        assert res["character_count"] == 25

    def test_dispatch_platform_message_invalid_platform(self) -> None:
        res = dispatch_platform_message("unknown_chat", "123", "Hello")
        assert res["status"] == "error"
        assert "Unsupported platform" in res["error"]

    def test_stream_ws_telemetry(self) -> None:
        payload = {"type": "agent_thinking", "tokens": 42}
        res = stream_ws_telemetry("sess_999", payload)
        assert res["status"] == "ok"
        assert res["event_type"] == "agent_thinking"
        assert res["subscribers_notified"] == 1

    def test_manage_scale_to_zero(self) -> None:
        res = manage_scale_to_zero(idle_timeout_seconds=600)
        assert res["status"] == "ok"
        assert res["idle_timeout_seconds"] == 600
        assert res["current_state"] == "ACTIVE"
