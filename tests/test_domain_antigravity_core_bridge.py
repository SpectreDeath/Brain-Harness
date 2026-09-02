"""Tests for Antigravity Core Bridge Plugin and Connection Service."""

from __future__ import annotations

import pytest
from plugins.agent_orchestration.antigravity_core_bridge.service import (
    AntigravityConnectionService,
    AntigravityCoreBridgePlugin,
    ANTIGRAVITY_CONNECTION_KEY,
    LocalStepObservation,
)
from harness.kernel.context import ServiceContext


@pytest.mark.unit
class TestAntigravityCoreBridge:
    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self) -> None:
        service = AntigravityConnectionService(host="127.0.0.1", port=4242)
        assert not service.is_connected

        connected = await service.connect()
        assert connected
        assert service.is_connected

        await service.disconnect()
        assert not service.is_connected

    @pytest.mark.asyncio
    async def test_session_creation_and_step_dispatch(self) -> None:
        service = AntigravityConnectionService()
        session = await service.create_session("sess_123", "You are an AI assistant.")
        assert session["session_id"] == "sess_123"
        assert session["status"] == "READY"

        observations = await service.dispatch_step("sess_123", "List files")
        assert len(observations) == 2
        assert observations[0].step_type == "PLANNER_RESPONSE"
        assert observations[1].step_type == "TOOL_CALL"
        assert observations[1].is_terminal

        status = service.get_session_status("sess_123")
        assert status is not None
        assert status["steps_count"] == 2

    @pytest.mark.asyncio
    async def test_plugin_ioc_lifecycle(self) -> None:
        plugin = AntigravityCoreBridgePlugin()
        assert ANTIGRAVITY_CONNECTION_KEY in plugin.provides

        ctx = ServiceContext()
        await plugin.on_load(ctx)
        resolved = ctx.require(ANTIGRAVITY_CONNECTION_KEY)
        assert resolved is not None

        await plugin.on_enable()
        assert resolved.is_connected
        await plugin.on_disable()
        assert not resolved.is_connected
