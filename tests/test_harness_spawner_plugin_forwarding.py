"""Unit & contract tests for HarnessSpawnerPlugin forwarding and CLI IoC routing (Rule 13, 45, 49)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from harness.cli import main
from harness.commands.spawn import get_spawner_service
from harness.kernel.context import ServiceContext
from harness.services.dock import DefaultDockService
from harness.services.harness_spawner import (
    HARNESS_SPAWNER_SERVICE_KEY,
    HarnessSpawnerProtocol,
    SpawnLifecycleState,
    SpawnSpec,
)
from harness.services.recursive_harnessing.models import BRAIN_SURFACE
from plugins.agent_orchestration.harness_spawner.main import HarnessSpawnerPlugin, plugin as spawner_plugin


@pytest.mark.unit
class TestHarnessSpawnerPluginForwarding:
    """Verify Step 2-4 parameter forwarding, IoC resolution, and CLI/plugin engine-state parity."""

    def test_plugin_forwards_all_step2_to_4_parameters_to_engine(self, tmp_path: Path) -> None:
        save_dir = tmp_path / "spawns"
        mat_dir = tmp_path / "mat_spawn"
        direct_mat_dir = tmp_path / "mat_direct"
        parent_lib = tmp_path / "parent_lib"
        parent_kn = tmp_path / "parent_kn"
        dock = DefaultDockService(workspace_root=tmp_path, state_file=tmp_path / "docks.json")

        scoped = HarnessSpawnerPlugin(state_file=save_dir / "registry.json")
        rec = scoped.spawn(
            SpawnSpec(
                name="fwd-worker",
                domain="security",
                task="audit policy",
                tree={"AGENTS.md": "# Security Worker\n\nAudit permissions.\n"},
                save_dir=save_dir,
            ),
            materialize_dir=mat_dir,
            dock_service=dock,
            approve_dock=True,
        )
        assert rec.state == SpawnLifecycleState.RUNNING
        assert Path(rec.materialized_dir).resolve() == mat_dir.resolve()
        assert rec.dock_name == "fwd-worker"
        assert (mat_dir / "dock.yaml").is_file()
        assert dock.run("fwd-worker", "validate").success
        assert scoped.export_dag().nodes[rec.node_id].status == "open"

        drift_clean = scoped.check_drift(
            mat_dir, BRAIN_SURFACE, expected_tree_sha256=rec.tree_sha256, dock_service=dock
        )
        assert drift_clean["drifted"] is False

        # propose_merge_back forwards proposal_kind
        prop_skill = scoped.propose_merge_back(
            rec.spawn_id,
            task_id="t-skill",
            cue="when auditing dock manifests",
            lesson="verify approval digest before procedure execution",
            evidence="unit contract",
            proposal_kind="skill",
        )
        assert prop_skill.proposal_kind == "skill"

        # adopt_merge_proposal forwards reviewer and review_note
        adopted = scoped.adopt_merge_proposal(
            prop_skill.proposal_id,
            parent_library_root=parent_lib,
            parent_knowledge_root=parent_kn,
            reviewer="alice",
            review_note="verified clean",
        )
        assert adopted["status"] == "adopted"
        assert adopted["reviewer"] == "alice"
        assert adopted["proposal_kind"] == "skill"

        # reject_merge_proposal forwards reviewer and reason without parent writes
        prop_rej = scoped.propose_merge_back(
            rec.spawn_id,
            task_id="t-rej",
            cue="when seeing warnings",
            lesson="ignore all warnings",
            evidence="single run",
            proposal_kind="ki",
        )
        rejected = scoped.reject_merge_proposal(prop_rej.proposal_id, reviewer="bob", reason="unsafe")
        assert rejected.status == "rejected"
        assert rejected.reviewer == "bob"
        assert rejected.review_note == "unsafe"
        assert not (parent_kn / prop_rej.ki_id).exists()

        # materialize forwards directly to materialize_spawn_as_dock
        mat_info = scoped.materialize(
            BRAIN_SURFACE,
            {"AGENTS.md": "# Direct Materialize\n"},
            direct_mat_dir,
            name="direct-dock",
            description="direct materialize via plugin",
            dock_service=dock,
            approve=True,
        )
        assert mat_info["dock_name"] == "direct-dock"
        assert mat_info["approved"] is True
        assert dock.run("direct-dock", "validate").success

        # DefaultHarnessSpawnerService.execute() forwards Step 2-4 actions & kwargs
        svc_mat_dir = tmp_path / "svc_exec_mat"
        exec_spawn = scoped._service.execute(
            "spawn",
            name="exec-worker",
            domain="audit",
            save_dir=save_dir,
            materialize_dir=svc_mat_dir,
            dock_service=dock,
            approve_dock=True,
        )
        assert exec_spawn["dock_name"] == "exec-worker"
        exec_prop = scoped.propose_merge_back(
            exec_spawn["spawn_id"],
            task_id="t-exec",
            cue="c",
            lesson="l",
            evidence="e",
            proposal_kind="config",
        )
        exec_rej = scoped._service.execute("reject", proposal_id=exec_prop.proposal_id, reviewer="eve", reason="hold")
        assert exec_rej["status"] == "rejected"
        assert exec_rej["reviewer"] == "eve"
        scoped.retire_all()

    def test_get_spawner_service_resolves_ioc_context_before_plugin_singleton(self, tmp_path: Path) -> None:
        ctx = ServiceContext()
        custom = HarnessSpawnerPlugin(state_file=tmp_path / "ioc.json")
        ctx.provide(HARNESS_SPAWNER_SERVICE_KEY, custom)

        resolved_ioc = get_spawner_service(save_dir=tmp_path / "other", context=ctx)
        assert resolved_ioc is custom

        resolved_fallback = get_spawner_service(save_dir=tmp_path / "cli_spawns")
        assert isinstance(resolved_fallback, HarnessSpawnerProtocol)
        assert resolved_fallback is not custom

    def test_cli_and_plugin_paths_reach_same_engine_state(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        docks_state = tmp_path / "docks.json"
        monkeypatch.setenv("HARNESS_DOCKS_STATE_FILE", str(docks_state))
        runner = CliRunner()

        # 1. CLI writes -> plugin reads exact same engine state
        cli_save = tmp_path / "cli_spawns"
        cli_mat = tmp_path / "cli_mat"
        res_run = runner.invoke(
            main,
            [
                "spawn",
                "run",
                "--name",
                "parity-cli",
                "--domain",
                "audit",
                "--task",
                "check parity",
                "--save-dir",
                str(cli_save),
                "--materialize",
                str(cli_mat),
                "--approve-dock",
            ],
        )
        assert res_run.exit_code == 0, res_run.output
        run_data = json.loads(res_run.output)
        spawn_id = run_data["spawn_id"]

        res_prop = runner.invoke(
            main,
            [
                "spawn",
                "propose",
                spawn_id,
                "--task-id",
                "p1",
                "--cue",
                "when auditing",
                "--lesson",
                "check SHA digests",
                "--evidence",
                "verified",
                "--kind",
                "skill",
                "--save-dir",
                str(cli_save),
            ],
        )
        assert res_prop.exit_code == 0, res_prop.output
        prop_id = json.loads(res_prop.output)["proposal_id"]

        res_rej = runner.invoke(
            main,
            [
                "spawn",
                "reject",
                prop_id,
                "--reviewer",
                "carol",
                "--reason",
                "needs second run",
                "--save-dir",
                str(cli_save),
            ],
        )
        assert res_rej.exit_code == 0, res_rej.output

        plugin_view = spawner_plugin.for_state_file(cli_save / "registry.json")
        rec_from_plugin = plugin_view.get_spawn(spawn_id)
        assert rec_from_plugin is not None
        assert rec_from_plugin.dock_name == "parity-cli"
        assert rec_from_plugin.tree_sha256 == run_data["tree_sha256"]
        assert Path(rec_from_plugin.materialized_dir).resolve() == cli_mat.resolve()
        proposals = plugin_view.list_proposals()
        assert len(proposals) == 1
        assert proposals[0].proposal_id == prop_id
        assert proposals[0].proposal_kind == "skill"
        assert proposals[0].status == "rejected"
        assert proposals[0].reviewer == "carol"
        assert proposals[0].review_note == "needs second run"

        # 2. Plugin writes -> CLI adopts & retires -> plugin sees exact adopted/retired state
        plug_save = tmp_path / "plug_spawns"
        plug_lib = tmp_path / "plug_lib"
        plug_kn = tmp_path / "plug_kn"
        plug_writer = spawner_plugin.for_state_file(plug_save / "registry.json")
        p_rec = plug_writer.spawn(
            SpawnSpec(
                name="parity-plug",
                domain="ops",
                tree={"AGENTS.md": "# Ops Harness\n"},
                save_dir=plug_save,
            )
        )
        p_prop = plug_writer.propose_merge_back(
            p_rec.spawn_id,
            task_id="p2",
            cue="when deploying",
            lesson="verify config bounds",
            evidence="staged test",
            proposal_kind="config",
        )

        res_adopt = runner.invoke(
            main,
            [
                "spawn",
                "adopt",
                p_prop.proposal_id,
                "--save-dir",
                str(plug_save),
                "--library-root",
                str(plug_lib),
                "--knowledge-root",
                str(plug_kn),
                "--reviewer",
                "dave",
                "--note",
                "lgtm",
            ],
        )
        assert res_adopt.exit_code == 0, res_adopt.output
        assert runner.invoke(main, ["spawn", "retire", p_rec.spawn_id, "--save-dir", str(plug_save)]).exit_code == 0

        reloaded = spawner_plugin.for_state_file(plug_save / "registry.json")
        assert reloaded.get_spawn(p_rec.spawn_id).state == SpawnLifecycleState.RETIRED  # type: ignore[union-attr]
        adopted_prop = reloaded.list_proposals(status="adopted")[0]
        assert adopted_prop.proposal_id == p_prop.proposal_id
        assert adopted_prop.proposal_kind == "config"
        assert adopted_prop.reviewer == "dave"
        assert adopted_prop.review_note == "lgtm"

    def test_cli_commands_dispatch_through_plugin_for_state_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HARNESS_DOCKS_STATE_FILE", str(tmp_path / "docks.json"))
        calls: list[Path] = []
        orig_for_state_file = spawner_plugin.for_state_file

        def _spy_for_state_file(state_file: Path | str | None) -> Any:
            calls.append(Path(state_file) if state_file is not None else Path())
            return orig_for_state_file(state_file)

        monkeypatch.setattr(spawner_plugin, "for_state_file", _spy_for_state_file)

        runner = CliRunner()
        save_dir = tmp_path / "spy_spawns"
        r1 = runner.invoke(main, ["spawn", "run", "--name", "spy", "--domain", "d", "--save-dir", str(save_dir)])
        assert r1.exit_code == 0, r1.output
        sid = json.loads(r1.output)["spawn_id"]

        assert runner.invoke(main, ["spawn", "list", "--save-dir", str(save_dir)]).exit_code == 0
        r_prop = runner.invoke(
            main,
            [
                "spawn",
                "propose",
                sid,
                "--task-id",
                "t1",
                "--cue",
                "c",
                "--lesson",
                "l",
                "--evidence",
                "e",
                "--save-dir",
                str(save_dir),
            ],
        )
        assert r_prop.exit_code == 0, r_prop.output
        pid = json.loads(r_prop.output)["proposal_id"]
        assert runner.invoke(main, ["spawn", "reject", pid, "--save-dir", str(save_dir)]).exit_code == 0
        assert runner.invoke(main, ["spawn", "retire", sid, "--save-dir", str(save_dir)]).exit_code == 0

        assert len(calls) == 5
        assert all(p == save_dir / "registry.json" for p in calls)

        drift_calls: list[Path] = []
        orig_check_drift = spawner_plugin.check_drift

        def _spy_check_drift(target_dir: Path | str, *args: Any, **kwargs: Any) -> dict[str, Any]:
            drift_calls.append(Path(target_dir))
            return orig_check_drift(target_dir, *args, **kwargs)

        monkeypatch.setattr(spawner_plugin, "check_drift", _spy_check_drift)
        mat_dir = tmp_path / "drift_mat"
        spawner_plugin.materialize(BRAIN_SURFACE, {"AGENTS.md": "# Drift\n"}, mat_dir, name="spy-drift")
        r_drift = runner.invoke(main, ["spawn", "check-drift", str(mat_dir)])
        assert r_drift.exit_code == 0, r_drift.output
        assert drift_calls == [mat_dir]
