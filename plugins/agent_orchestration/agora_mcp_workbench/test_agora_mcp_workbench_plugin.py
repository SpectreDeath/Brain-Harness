"""Contract tests for agora_mcp_workbench plugin (Rule 34, Rule 38, Rule 45)."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.creator.validator import PluginValidator  # noqa: E402
from harness.kernel.context import ServiceContext  # noqa: E402
from harness.services.agora_workbench import (  # noqa: E402
    AGORA_WORKBENCH_SERVICE_KEY,
    AgoraWorkbenchProtocol,
)
from plugins.agent_orchestration.agora_mcp_workbench.main import (  # noqa: E402
    agora_audit_sidecar,
    agora_evaluate_connector,
    agora_plan_state_workflow,
    agora_validate_datalake_transfer,
    plugin,
)


def test_agora_plugin_entrypoints() -> None:
    sidecar = agora_audit_sidecar(
        name="model-daemon",
        command=["-m", "model_srv"],
        url_env_var="MODEL_DAEMON_URL",
        port=8500,
    )
    assert sidecar["valid"] is True
    assert sidecar["locked_port"] == 8500

    plan = agora_plan_state_workflow(
        source_state="s.a",
        target_state="s.b",
        tools=[{"name": "t1", "server": "srv", "requires": ["s.a"], "produces": ["s.b"]}],
    )
    assert plan["reachable"] is True
    assert len(plan["steps"]) == 1

    conn = agora_evaluate_connector(
        mode="gateway",
        code="safe_call()",
        blocked_tools=["parallel_execute"],
        allowed_tools=["safe_call"],
        calls_in_last_minute=2,
        max_calls_per_minute=10,
    )
    assert conn["allowed"] is True
    assert conn["suppressed_companions"] == ("poll_batch", "collect_batch", "cancel_batch")

    dl = agora_validate_datalake_transfer(
        policy_mode="homogeneous_source",
        has_per_artifact_enforcer=False,
        requested_sources=["local"],
        permitted_sources=["local"],
    )
    assert dl["valid"] is True
    assert dl["effective_sources"] == ("local",)


@pytest.mark.asyncio
async def test_agora_plugin_lifecycle_and_validator() -> None:
    ctx = ServiceContext()
    await plugin.on_load(ctx)
    resolved = ctx.require(AGORA_WORKBENCH_SERVICE_KEY)
    assert isinstance(resolved, AgoraWorkbenchProtocol)

    report = await PluginValidator().validate(Path(__file__).resolve().parent)
    assert report.valid, f"Plugin validation failed: {[c.message for c in report.checks if not c.passed]}"
