"""Tests for Google ADK Runtime Plugin."""

import pytest
from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.google_adk_runtime.main import (
    GOOGLE_ADK_RUNTIME_SERVICE_KEY,
    GoogleAdkRuntimePlugin,
)

@pytest.mark.asyncio
async def test_google_adk_runtime_lifecycle_and_tools():
    ctx = ServiceContext()
    p = GoogleAdkRuntimePlugin()
    await p.enable(ctx)

    service = ctx.require(GOOGLE_ADK_RUNTIME_SERVICE_KEY)
    assert service is not None

    # Test run_agent
    res = service.run_agent("evaluator", "Assess trajectory quality", "test_sess")
    assert res["status"] == "success"
    assert res["session_id"] == "test_sess"
    assert res["turn_count"] == 2

    # Test list_sessions
    sessions = service.list_sessions()
    assert sessions["status"] == "success"
    assert sessions["total_sessions"] >= 1

    # Test rewind_session
    rewind = service.rewind_session("test_sess", 0)
    assert rewind["status"] == "success"
    assert rewind["remaining_events"] == 1

    # Test register_skill
    reg = service.register_skill("code_analyst", "Analyzes code style", "System: Check PEP8")
    assert reg["status"] == "success"
    assert reg["skill_name"] == "code_analyst"

    await p.disable(ctx)
