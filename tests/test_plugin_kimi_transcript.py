"""Unit tests for Kimi Transcript Plugin and Scope Inspector."""

import pytest
from pathlib import Path

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.kimi_bridge import (
    KIMI_TRANSCRIPT_KEY,
    KimiTranscriptService,
    ScopeAnnotation,
    TranscriptFrame,
)
from plugins.agent_orchestration.kimi_transcript.main import (
    KimiTranscriptPlugin,
    KimiTranscriptServiceImpl,
    TranscriptProjectionEngine,
    ScopeInspector,
    kimi_transcript_project,
    kimi_scope_inspect,
)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_plugin_manifest_validation() -> None:
    """Validate that plugin.kimi_transcript manifest passes all PluginValidator checks."""
    plugin_dir = Path("plugins/agent_orchestration/kimi_transcript")
    assert plugin_dir.exists(), "Plugin directory must exist"

    report = await PluginValidator.validate(plugin_dir)
    assert report.valid, f"Plugin manifest validation failed: {report.errors}"
    assert len(report.errors) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_plugin_lifecycle_and_service_registration() -> None:
    """Test enabling KimiTranscriptPlugin registers KIMI_TRANSCRIPT_KEY into context."""
    context = ServiceContext()
    plugin = KimiTranscriptPlugin()

    await plugin.on_enable(context)
    assert context.has(KIMI_TRANSCRIPT_KEY)

    service = context.require(KIMI_TRANSCRIPT_KEY)
    assert service is not None
    assert isinstance(service, KimiTranscriptService)

    await plugin.on_disable(context)


@pytest.mark.unit
def test_transcript_granularity_filtering() -> None:
    """Test filtering event streams across off, turn, block, and delta granularity levels."""
    engine = TranscriptProjectionEngine()

    sample_events = [
        {"event_type": "turn_start", "payload": {"turn": 1}},
        {"event_type": "token_delta", "payload": {"text": "Thinking..."}},
        {"event_type": "token_delta", "payload": {"text": "Processing"}},
        {"event_type": "tool_call", "payload": {"tool": "git_status"}},
        {"event_type": "tool_result", "payload": {"output": "clean"}},
        {"event_type": "agent_response", "payload": {"msg": "Done"}},
        {"event_type": "turn_complete", "payload": {"turn": 1}},
    ]

    # 1. 'off' granularity
    res_off = engine.project(sample_events, granularity="off")
    assert res_off["total_count"] == 0
    assert len(res_off["frames"]) == 0

    # 2. 'turn' granularity (turn_start, agent_response, turn_complete)
    res_turn = engine.project(sample_events, granularity="turn")
    assert res_turn["total_count"] == 3
    assert [f["event_type"] for f in res_turn["frames"]] == [
        "turn_start",
        "agent_response",
        "turn_complete",
    ]

    # 3. 'block' granularity (turn events + tool_call, tool_result)
    res_block = engine.project(sample_events, granularity="block")
    assert res_block["total_count"] == 5
    assert "token_delta" not in [f["event_type"] for f in res_block["frames"]]
    assert "tool_call" in [f["event_type"] for f in res_block["frames"]]

    # 4. 'delta' granularity (all 7 events)
    res_delta = engine.project(sample_events, granularity="delta")
    assert res_delta["total_count"] == 7


@pytest.mark.asyncio
@pytest.mark.unit
async def test_transcript_pagination() -> None:
    """Test cursor-based pagination on projected transcript frames."""
    sample_events = [{"event_type": "turn_start", "payload": {"idx": i}} for i in range(25)]

    page1 = await kimi_transcript_project(frames=sample_events, granularity="delta", cursor=0, limit=10)
    assert page1["returned_count"] == 10
    assert page1["has_more"] is True
    assert page1["next_cursor"] == 10

    page2 = await kimi_transcript_project(frames=sample_events, granularity="delta", cursor=10, limit=10)
    assert page2["returned_count"] == 10
    assert page2["has_more"] is True
    assert page2["next_cursor"] == 20

    page3 = await kimi_transcript_project(frames=sample_events, granularity="delta", cursor=20, limit=10)
    assert page3["returned_count"] == 5
    assert page3["has_more"] is False
    assert page3["next_cursor"] is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_scope_inspector_4tier_hierarchy() -> None:
    """Test inspecting 4-tier nested ServiceContext tree (APP -> WORKSPACE -> SESSION -> AGENT)."""
    root_app = ServiceContext()
    workspace_ctx = root_app.child()
    session_ctx = workspace_ctx.child()
    agent_ctx = session_ctx.child()

    report = await kimi_scope_inspect(context=agent_ctx)
    assert report["status"] == "ok"
    assert report["total_depth"] == 4

    scopes = report["scopes"]
    assert scopes[0]["scope_type"] == "app"
    assert scopes[0]["depth"] == 0

    assert scopes[1]["scope_type"] == "workspace"
    assert scopes[1]["depth"] == 1

    assert scopes[2]["scope_type"] == "session"
    assert scopes[2]["depth"] == 2

    assert scopes[3]["scope_type"] == "agent"
    assert scopes[3]["depth"] == 3
