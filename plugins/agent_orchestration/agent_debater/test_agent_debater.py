"""Tests for Agent Debater Adapter Plugin."""

from pathlib import Path
import pytest
import sys

_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.agent_debater.main import (
    conduct_dialectical_debate,
    synthesize_debate_verdict,
    plugin,
    CRITIC_EVALUATION_SERVICE_KEY,
)


def test_debater_tool_functions() -> None:
    debate = conduct_dialectical_debate("Test Topic", ["Pro 1"], ["Con 1", "Con 2"])
    assert debate["total_rounds"] == 2
    assert debate["pro_points_count"] == 1
    assert debate["con_points_count"] == 2

    verdict = synthesize_debate_verdict(debate)
    assert verdict["status"] == "ok"
    assert "Arbiter Verdict" in verdict["verdict_markdown"]


@pytest.mark.asyncio
async def test_agent_debater_plugin_lifecycle() -> None:
    context = ServiceContext()
    await plugin.enable(context)

    resolved = context.require(CRITIC_EVALUATION_SERVICE_KEY)
    assert resolved is not None
    assert hasattr(resolved, "conduct_dialectical_debate")

    await plugin.disable(context)
