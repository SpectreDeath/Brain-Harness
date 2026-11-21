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
from harness.services.dock import DefaultDockService  # noqa: E402
from harness.services.harness_spawner import (  # noqa: E402
    HARNESS_SPAWNER_SERVICE_KEY,
    HarnessSpawnerProtocol,
    SpawnLifecycleState,
    SpawnSpec,
)
from harness.services.recursive_harnessing.models import BRAIN_SURFACE  # noqa: E402
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


@pytest.mark.unit
def test_plugin_singleton_forwards_step2_to_4_methods(tmp_path: Path) -> None:
    """Verify plugin singleton exposes materialize_dir, proposal_kind, reviewer, reject, and materialize."""
    dock = DefaultDockService(workspace_root=tmp_path, state_file=tmp_path / "docks.json")
    mat_dir = tmp_path / "plug_mat"
    direct_dir = tmp_path / "plug_direct"
    rec = plugin.spawn(
        SpawnSpec(
            name="singleton-fwd",
            domain="audit",
            tree={"AGENTS.md": "# Singleton Forward\n"},
            save_dir=tmp_path / "spawns",
        ),
        materialize_dir=mat_dir,
        dock_service=dock,
        approve_dock=True,
    )
    try:
        assert rec.dock_name == "singleton-fwd"
        assert (mat_dir / "dock.yaml").is_file()

        p_ok = plugin.propose_merge_back(
            rec.spawn_id,
            task_id="t1",
            cue="c1",
            lesson="l1",
            evidence="e1",
            proposal_kind="skill",
        )
        adopted = plugin.adopt_merge_proposal(
            p_ok.proposal_id,
            parent_library_root=tmp_path / "lib",
            parent_knowledge_root=tmp_path / "kn",
            reviewer="alice",
            review_note="ok",
        )
        assert adopted["reviewer"] == "alice"
        assert adopted["proposal_kind"] == "skill"

        p_bad = plugin.propose_merge_back(
            rec.spawn_id,
            task_id="t2",
            cue="c2",
            lesson="l2",
            evidence="e2",
        )
        rejected = plugin.reject_merge_proposal(p_bad.proposal_id, reviewer="bob", reason="no")
        assert rejected.status == "rejected"
        assert rejected.reviewer == "bob"

        mat_res = plugin.materialize(
            BRAIN_SURFACE,
            {"AGENTS.md": "# Direct\n"},
            direct_dir,
            name="direct-singleton",
            description="direct materialize",
            dock_service=dock,
            approve=True,
        )
        assert mat_res["dock_name"] == "direct-singleton"
        assert mat_res["approved"] is True
    finally:
        plugin.retire(rec.spawn_id)
