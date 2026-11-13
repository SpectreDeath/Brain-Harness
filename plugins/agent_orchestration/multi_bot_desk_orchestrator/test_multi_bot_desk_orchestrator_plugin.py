"""Contract tests for Multi-Bot Desk Orchestrator Plugin."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.creator.validator import PluginValidator  # noqa: E402
from harness.kernel.context import ServiceContext  # noqa: E402
from harness.services.multi_bot_desk import MULTI_BOT_DESK_SERVICE_KEY  # noqa: E402
from plugins.agent_orchestration.multi_bot_desk_orchestrator.main import (  # noqa: E402
    desk_allocate_lease,
    desk_evaluate_bot_hop,
    desk_evaluate_mcp_approval,
    plugin,
)


def test_desk_entrypoints() -> None:
    hop = desk_evaluate_bot_hop("bot-a", "bot-b", "hello", current_depth=3, max_depth=3)
    assert hop["allowed"] is False

    approval = desk_evaluate_mcp_approval("bot-a", "github_create_issue", is_read_only=False)
    assert approval["decision"] == "require_approval"
    assert approval["blocks_turn"] is True

    lease = desk_allocate_lease("bot-b", is_primary=False, occupied_displays=[1])
    assert lease["display_index"] == 2
    assert lease["gateway_port"] == 8652
    assert lease["cdp_port"] == 9202


@pytest.mark.asyncio
async def test_desk_plugin_lifecycle_and_validator() -> None:
    context = ServiceContext()
    await plugin.enable(context)
    resolved = context.require(MULTI_BOT_DESK_SERVICE_KEY)
    assert resolved is plugin
    await plugin.disable(context)

    report = PluginValidator().validate_sync(Path(__file__).resolve().parent)
    assert report.valid, f"Plugin validation failed: {[c.message for c in report.checks if not c.passed]}"


@pytest.mark.asyncio
async def test_plugin_serial_turn_queue() -> None:
    import asyncio

    order: list[str] = []

    async def step(tag: str, delay: float) -> str:
        order.append(f"start:{tag}")
        await asyncio.sleep(delay)
        order.append(f"end:{tag}")
        return tag

    r1, r2 = await asyncio.gather(
        plugin.enqueue_bot_turn("bot-x", lambda: step("1", 0.02)),
        plugin.enqueue_bot_turn("bot-x", lambda: step("2", 0.01)),
    )
    assert (r1, r2) == ("1", "2")
    assert order == ["start:1", "end:1", "start:2", "end:2"]
