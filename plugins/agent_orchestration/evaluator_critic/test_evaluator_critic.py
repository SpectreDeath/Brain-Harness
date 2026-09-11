"""Tests for Evaluator Critic Adapter Plugin."""

from pathlib import Path
import pytest
import sys

_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.evaluator_critic.main import (
    critic_check_safety,
    critic_evaluate_code,
    critic_review_plan,
    plugin,
    CRITIC_EVALUATION_SERVICE_KEY,
)


def test_adapter_tool_functions() -> None:
    # Safety check
    res_safe = critic_check_safety("echo 'hello'")
    assert res_safe["is_safe"] is True

    res_danger = critic_check_safety("rm -rf /")
    assert res_danger["is_safe"] is False

    # Code evaluation
    res_code = critic_evaluate_code("def foo():\n    return 42\n", "python")
    assert res_code["valid"] is True

    # Plan review
    res_plan = critic_review_plan("Deploy", ["Update files", "Run verify test"])
    assert res_plan["has_verification_step"] is True


@pytest.mark.asyncio
async def test_evaluator_critic_plugin_lifecycle() -> None:
    context = ServiceContext()
    await plugin.enable(context)

    resolved = context.require(CRITIC_EVALUATION_SERVICE_KEY)
    assert resolved is not None
    assert hasattr(resolved, "check_command_safety")

    await plugin.disable(context)
