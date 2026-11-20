"""Tests for dock materialization, drift detection, and merge-back policy enforcement (Tracks 2 & 3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from harness.cli import main
from harness.services.harness_spawner import (
    HarnessSpawnerEngine,
    SpawnSpec,
    check_materialized_drift,
)
from harness.services.recursive_harnessing.library import ExperienceLibrary
from harness.services.recursive_harnessing.models import BRAIN_SURFACE


@pytest.mark.unit
class TestSpawnMaterializeAndMergePolicy:
    """Verify `--materialize` dock lifecycle, drift detection, and reviewed-only merge policy."""

    def test_materialize_link_inspect_run_list_and_drift(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        docks_state = tmp_path / "docks.json"
        monkeypatch.setenv("HARNESS_DOCKS_STATE_FILE", str(docks_state))

        save_dir = tmp_path / "spawns"
        mat_dir = tmp_path / "domain_repo"
        runner = CliRunner()

        res_run = runner.invoke(
            main,
            [
                "spawn",
                "run",
                "--name",
                "finance-auditor",
                "--domain",
                "finance",
                "--task",
                "audit ledger totals",
                "--save-dir",
                str(save_dir),
                "--materialize",
                str(mat_dir),
                "--approve-dock",
            ],
        )
        assert res_run.exit_code == 0, res_run.output
        run_data = json.loads(res_run.output)
        assert run_data["state"] == "RUNNING"
        assert Path(run_data["materialized_dir"]).resolve() == mat_dir.resolve()
        assert run_data["dock_name"] == "finance-auditor"
        assert (mat_dir / "dock.yaml").is_file()
        assert (mat_dir / "AGENTS.md").is_file()

        res_list = runner.invoke(main, ["spawn", "list", "--save-dir", str(save_dir)])
        assert res_list.exit_code == 0, res_list.output
        assert json.loads(res_list.output)["count"] == 1

        res_inspect = runner.invoke(main, ["dock", "inspect", str(mat_dir)])
        assert res_inspect.exit_code == 0, res_inspect.output
        assert "finance-auditor" in res_inspect.output

        res_dock_run = runner.invoke(main, ["dock", "run", "finance-auditor", "validate"])
        assert res_dock_run.exit_code == 0, res_dock_run.output
        assert "DOCK_HARNESS_OK" in res_dock_run.output

        # Clean check-drift passes
        res_clean = runner.invoke(
            main,
            ["spawn", "check-drift", str(mat_dir), "--expected-digest", run_data["tree_sha256"]],
        )
        assert res_clean.exit_code == 0, res_clean.output
        assert not json.loads(res_clean.output)["drifted"]

        # Mutate AGENTS.md -> tree drift detected and rejected by check-drift
        (mat_dir / "AGENTS.md").write_text("# Tampered\n", encoding="utf-8")
        res_drifted = runner.invoke(
            main,
            ["spawn", "check-drift", str(mat_dir), "--expected-digest", run_data["tree_sha256"]],
        )
        assert res_drifted.exit_code == 1
        drift_payload = json.loads(res_drifted.output)
        assert drift_payload["tree_drifted"] is True
        assert drift_payload["drifted"] is True

        # Mutate dock.yaml -> manifest_changed detected via dock list_docks()
        (mat_dir / "dock.yaml").write_text(
            (mat_dir / "dock.yaml").read_text(encoding="utf-8") + "\n# mutated\n",
            encoding="utf-8",
        )
        manifest_report = check_materialized_drift(
            mat_dir,
            BRAIN_SURFACE,
            expected_tree_sha256=run_data["tree_sha256"],
            dock_name="finance-auditor",
        )
        assert manifest_report["dock_status"] == "manifest_changed"
        assert manifest_report["manifest_drifted"] is True

    def test_generated_dock_yaml_does_not_depend_on_bare_python(self) -> None:
        import sys

        from harness.services.harness_spawner.materialize import build_spawn_dock_yaml

        payload = build_spawn_dock_yaml(
            name="portable", description="", surface=BRAIN_SURFACE, tree={"AGENTS.md": "# Portable\n"}
        )
        command = payload["entrypoints"]["validate"]["steps"][0]["command"]
        assert not command.startswith("python "), command
        assert sys.executable in command
        assert "DOCK_HARNESS_OK" in command

    def test_merge_back_policy_adopt_reject_and_protected_block(self, tmp_path: Path) -> None:
        save_dir = tmp_path / "spawns"
        parent_lib = tmp_path / "parent_lib"
        parent_kn = tmp_path / "parent_kn"

        engine = HarnessSpawnerEngine(state_file=save_dir / "registry.json")
        rec = engine.spawn(
            SpawnSpec(
                name="worker-merge",
                domain="security",
                tree={"AGENTS.md": "# Security Worker\n\nAudit permissions.\n"},
                save_dir=save_dir,
            )
        )

        # Protected path CLAUDE.md / dock.yaml blocked by policy
        with pytest.raises(ValueError, match="protected target"):
            engine.propose_merge_back(
                rec.spawn_id,
                task_id="bad-cfg",
                cue="when configuring",
                lesson="overwrite governance",
                evidence="none",
                tree={"AGENTS.md": "# Ok\n", "CLAUDE.md": "# Blocked\n"},
                proposal_kind="config",
            )

        # Rejected proposal lands nowhere in parent stores
        prop_rej = engine.propose_merge_back(
            rec.spawn_id,
            task_id="t-reject",
            cue="when noisy logs appear",
            lesson="silence all warnings",
            evidence="single run",
            proposal_kind="ki",
        )
        rejected = engine.reject_merge_proposal(prop_rej.proposal_id, reviewer="alice", reason="unsafe")
        assert rejected.status == "rejected"
        assert rejected.reviewer == "alice"
        assert not (parent_kn / prop_rej.ki_id).exists()
        assert ExperienceLibrary(parent_lib, "security", BRAIN_SURFACE).entries() == []
        with pytest.raises(ValueError, match="rejected"):
            engine.adopt_merge_proposal(
                prop_rej.proposal_id,
                parent_library_root=parent_lib,
                parent_knowledge_root=parent_kn,
            )

        # Approved proposal adopts cleanly into parent library & dual-file KI
        prop_ok = engine.propose_merge_back(
            rec.spawn_id,
            task_id="t-adopt",
            cue="when checking shell safety",
            lesson="reject credential reads before execution",
            evidence="verified on 3 safety cases",
            proposal_kind="skill",
        )
        adopted = engine.adopt_merge_proposal(
            prop_ok.proposal_id,
            parent_library_root=parent_lib,
            parent_knowledge_root=parent_kn,
            reviewer="bob",
            review_note="verified",
        )
        assert adopted["status"] == "adopted"
        assert adopted["reviewer"] == "bob"
        assert adopted["proposal_kind"] == "skill"
        assert (parent_kn / prop_ok.ki_id / "metadata.json").is_file()
        assert (parent_kn / prop_ok.ki_id / "summary.md").is_file()
        assert len(ExperienceLibrary(parent_lib, "security", BRAIN_SURFACE).entries()) == 1
        engine.retire_all()
