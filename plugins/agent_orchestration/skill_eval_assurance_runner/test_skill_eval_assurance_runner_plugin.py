"""Contract tests for skill_eval_assurance_runner plugin (Rule 34, Rule 38, Rule 45)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.creator.validator import PluginValidator  # noqa: E402
from harness.kernel.context import ServiceContext  # noqa: E402
from harness.services.skill_eval_assurance import (  # noqa: E402
    SKILL_EVAL_ASSURANCE_SERVICE_KEY,
    SkillEvalAssuranceProtocol,
)
from plugins.agent_orchestration.skill_eval_assurance_runner.main import (  # noqa: E402
    assurance_grade_action_sequence,
    assurance_grade_tool_constraints,
    assurance_pass_hat_k,
    assurance_verify_sealed_envelope,
    assurance_wilson_ci,
    plugin,
)


def test_assurance_entrypoints() -> None:
    ci = assurance_wilson_ci(4, 5, 0.95)
    assert 0.0 <= ci["lower"] < ci["mean"] < ci["upper"] <= 1.0

    pk = assurance_pass_hat_k(4, 5, 2)
    assert pk["pass_hat_k"] == pytest.approx(0.6)

    seq = assurance_grade_action_sequence(
        ["read_file", "run_command", "edit_file"],
        ["read_file", "edit_file"],
        "in_order_match",
    )
    assert seq["passed"] is True
    assert seq["recall"] == pytest.approx(1.0)

    tools = assurance_grade_tool_constraints(
        ["read_file", "run_command"],
        expect_tools=["read_file"],
        reject_tools=["rm -rf"],
        allow_only=True,
    )
    assert tools["passed"] is False
    assert any("disallowed_tool:run_command" in v for v in tools["violations"])

    digest = plugin.seal_json_envelope({"accepted": True, "score": 0.9})
    verified = assurance_verify_sealed_envelope(
        {"accepted": True, "score": 0.9, "digest": digest}
    )
    assert verified["valid"] is True


@pytest.mark.asyncio
async def test_assurance_plugin_lifecycle_and_validator() -> None:
    ctx = ServiceContext()
    await plugin.on_load(ctx)
    resolved = ctx.require(SKILL_EVAL_ASSURANCE_SERVICE_KEY)
    assert isinstance(resolved, SkillEvalAssuranceProtocol)

    report = await PluginValidator().validate(Path(__file__).resolve().parent)
    assert report.valid, f"Plugin validation failed: {[c.message for c in report.checks if not c.passed]}"
