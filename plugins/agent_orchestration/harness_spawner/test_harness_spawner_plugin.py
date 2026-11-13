"""Contract tests for the harness_spawner plugin (Rules 34, 38, 44, 45)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.creator.validator import PluginValidator  # noqa: E402
from harness.kernel.context import ServiceContext  # noqa: E402
from harness.services.harness_spawner import (  # noqa: E402
    HARNESS_SPAWNER_SERVICE_KEY,
    HarnessSpawnerProtocol,
    SpawnLifecycleState,
)
from plugins.agent_orchestration.harness_spawner.main import (  # noqa: E402
    plugin,
    spawn_child_harness,
)


def test_spawn_child_harness_entrypoint(tmp_path: Path) -> None:
    """Verify module tool entrypoint spawns and retires cleanly via plugin singleton."""
    result = spawn_child_harness(
        name="worker-a",
        domain="verification",
        task="check plugin entrypoint",
        max_tokens=4000,
        save_dir=tmp_path / "spawns",
    )
    assert result["state"] == SpawnLifecycleState.RUNNING.value
    assert result["depth"] == 1
    assert result["domain"] == "verification"
    retired = plugin.retire(result["spawn_id"])
    assert retired.state == SpawnLifecycleState.RETIRED


@pytest.mark.asyncio
async def test_harness_spawner_plugin_lifecycle_and_validator() -> None:
    """Verify IoC resolution, parent disposal cascade, and PluginValidator compliance."""
    ctx = ServiceContext()
    await plugin.on_load(ctx)
    resolved = ctx.require(HARNESS_SPAWNER_SERVICE_KEY)
    assert isinstance(resolved, HarnessSpawnerProtocol)

    report = await PluginValidator().validate(Path(__file__).resolve().parent)
    assert report.valid, f"Plugin validation failed: {[c.message for c in report.checks if not c.passed]}"
    await ctx.dispose()
