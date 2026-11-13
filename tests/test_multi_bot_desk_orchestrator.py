"""Contract tests for Multi-Bot Desk Orchestrator skill, models, and service."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.services.multi_bot_desk import (
    MULTI_BOT_DESK_SERVICE_KEY,
    BotHopDispatchRequest,
    McpApprovalRequest,
    MultiBotDeskEngine,
    MultiBotDeskProtocol,
)


@pytest.mark.unit
class TestMultiBotDeskModelsAndEngine:
    def test_frozen_slotted_immutability(self) -> None:
        """Verify Rule 12 & Rule 43 immutability via direct attribute assignment."""
        req = BotHopDispatchRequest(
            from_bot_id="bot-a",
            to_bot_id="bot-b",
            message_text="hi",
        )
        with pytest.raises((AttributeError, TypeError)):
            req.current_depth = 2  # type: ignore[misc]

        mcp_req = McpApprovalRequest(bot_id="bot-a", tool_name="send_email")
        with pytest.raises((AttributeError, TypeError)):
            mcp_req.is_read_only = True  # type: ignore[misc]

    def test_hop_depth_and_room_fanout_bounds(self) -> None:
        engine = MultiBotDeskEngine()
        ok = engine.evaluate_bot_hop_dispatch(
            BotHopDispatchRequest("bot-a", "bot-b", "ping", current_depth=1, max_depth=3)
        )
        assert ok.allowed is True
        assert ok.next_depth == 2

        capped = engine.evaluate_bot_hop_dispatch(
            BotHopDispatchRequest("bot-a", "bot-b", "ping", current_depth=3, max_depth=3)
        )
        assert capped.allowed is False

        room = engine.evaluate_bot_hop_dispatch(
            BotHopDispatchRequest(
                from_bot_id="user",
                to_bot_id="room-1",
                message_text="hello team",
                is_room_broadcast=True,
                room_member_ids=("bot-1", "bot-2", "bot-3", "bot-4"),
            )
        )
        assert room.allowed is True
        assert room.target_bot_ids == ("bot-1", "bot-2", "bot-3")

    def test_mcp_approval_and_desk_leases(self) -> None:
        engine = MultiBotDeskEngine()
        assert (
            engine.evaluate_mcp_tool_approval(
                McpApprovalRequest("bot-a", "read_file", is_read_only=True)
            ).decision
            == "auto_allow"
        )
        assert (
            engine.evaluate_mcp_tool_approval(
                McpApprovalRequest(
                    "bot-a",
                    "send_email",
                    always_allowed_tools=("send_email",),
                )
            ).decision
            == "auto_allow"
        )
        assert (
            engine.evaluate_mcp_tool_approval(
                McpApprovalRequest("bot-a", "send_email", user_interrupted=True)
            ).decision
            == "skipped"
        )

        primary = engine.allocate_bot_desk_lease("primary", is_primary=True)
        assert primary.display_index == 0
        assert primary.mutates_primary_config is False

        managed = engine.allocate_bot_desk_lease("bot-2", occupied_displays=(1,))
        assert managed.display_index == 2
        assert managed.gateway_port == 8652
        assert managed.cdp_port == 9202

        assert isinstance(engine, MultiBotDeskProtocol)
        assert MULTI_BOT_DESK_SERVICE_KEY.name == "service.multi_bot_desk_orchestrator"

    def test_skill_package_validation(self) -> None:
        from harness.creator.skills import SkillValidator

        skill_dir = (
            Path(__file__).resolve().parent.parent
            / ".agents"
            / "skills"
            / "multi-bot-desk-orchestrator"
        )
        report = SkillValidator().validate(skill_dir)
        assert report.valid, f"Skill validation failed: {[c.message for c in report.checks if not c.passed]}"
