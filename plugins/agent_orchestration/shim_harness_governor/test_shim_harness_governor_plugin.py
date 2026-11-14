"""Contract & entrypoint tests for plugin.shim_harness_governor."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_SRC_DIR = _REPO_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

from harness.creator.validator import PluginValidator  # noqa: E402
from harness.kernel.context import ServiceContext  # noqa: E402
from harness.services.shim_harness_governor import (  # noqa: E402
    SHIM_HARNESS_GOVERNOR_KEY,
    ShimHarnessGovernorProtocol,
)
import main as plugin_main  # noqa: E402


@pytest.mark.asyncio
async def test_shim_plugin_validates_with_plugin_validator() -> None:
    report = await PluginValidator().validate(_PLUGIN_DIR)
    assert report.valid, [f"{c.rule}: {c.message}" for c in report.checks if not c.passed]


@pytest.mark.asyncio
async def test_shim_plugin_ioc_lifecycle_and_entrypoints(tmp_path: Path) -> None:
    ctx = ServiceContext()
    await plugin_main.plugin.on_load(ctx)
    resolved = ctx.require(SHIM_HARNESS_GOVERNOR_KEY)
    assert isinstance(resolved, ShimHarnessGovernorProtocol)

    tool_res = plugin_main.shim_audit_tool_execution(
        permission_mode="ask",
        tool_level="write",
        workspace_root=str(tmp_path),
        target_path="out.txt",
        confirmed=True,
    )
    assert tool_res["allowed"] is True

    route_res = plugin_main.shim_route_command("help")
    assert route_res["resolved_command"] == "/help"
    assert route_res["allowlisted"] is True

    mcp_res = plugin_main.shim_audit_mcp_discovery(
        server_name="git",
        tool_names=["status", "diff"],
        config_payload={"version": 1, "permissions": "ask", "api": "openai", "api_key_env": "OPENAI_API_KEY"},
    )
    assert mcp_res["violations"] == ()

    sess_res = plugin_main.shim_audit_session_skills(
        session_id="20261114-133500-01020304",
        skill_candidates=[{"name": "demo", "tier": ".agents/skills", "size_bytes": 128}],
    )
    assert sess_res["session_id_valid"] is True
    assert sess_res["winning_skills"] == ("demo@.agents/skills",)

    await plugin_main.plugin.on_disable()
