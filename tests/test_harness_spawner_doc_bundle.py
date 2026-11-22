"""Contract and portability tests for 7-part harness docs & drift digest (Track 2.3)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from click.testing import CliRunner
import pytest

from harness.cli import main
from harness.services.dock import DefaultDockService
from harness.services.dock.safety import _build_scrubbed_env
from harness.services.harness_spawner import (
    HarnessBlueprint,
    build_blueprint_tree,
    materialize_spawn_as_dock,
    recommend_harness_blueprints,
    run_cold_walk,
    validate_harness_docs,
)
from harness.services.icm_architect import IcmAuditor, IcmVerifier
from harness.services.recursive_harnessing.models import BRAIN_SURFACE


@pytest.fixture(scope="module")
def distiller_bundle() -> tuple[HarnessBlueprint, dict[str, str]]:
    bp = recommend_harness_blueprints(name="harness-repo-distiller")[0]
    return bp, build_blueprint_tree(bp)


@pytest.fixture(scope="module")
def security_bundle() -> tuple[HarnessBlueprint, dict[str, str]]:
    bp = recommend_harness_blueprints(name="harness-security-forensics")[0]
    return bp, build_blueprint_tree(bp)


@pytest.mark.unit
class TestHarnessSpawnerDocBundle:
    """Verify 7-part doc generation, missing-doc failures, PATH portability, ICM checks, and doc drift."""

    @pytest.mark.parametrize(
        "blueprint_name,expected_form",
        [
            ("harness-repo-distiller", "knowledge_bundle"),
            ("harness-security-forensics", "record_library"),
        ],
    )
    def test_materialized_blueprint_passes_docs_icm_and_portable_dock_run(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        blueprint_name: str,
        expected_form: str,
    ) -> None:
        docks_state = tmp_path / "docks.json"
        monkeypatch.setenv("HARNESS_DOCKS_STATE_FILE", str(docks_state))
        save_dir = tmp_path / "spawns"
        mat_dir = tmp_path / blueprint_name
        runner = CliRunner()

        res_rev = runner.invoke(main, ["spawn", "review", "--blueprint", blueprint_name, "--json"])
        assert res_rev.exit_code == 0, res_rev.output
        expected_digest = json.loads(res_rev.output)["tree_sha256"]

        res_run = runner.invoke(
            main,
            [
                "spawn",
                "run",
                "--blueprint",
                blueprint_name,
                "--save-dir",
                str(save_dir),
                "--materialize",
                str(mat_dir),
                "--approve-dock",
                "--write-permitted",
                "--approve-digest",
                expected_digest,
            ],
        )
        assert res_run.exit_code == 0, res_run.output
        run_data: dict[str, Any] = json.loads(res_run.output)
        assert run_data["tree_sha256"] == expected_digest

        # 2.3(c) 7-part docs validator + IcmAuditor + IcmVerifier clean
        doc_val = validate_harness_docs(mat_dir)
        assert doc_val["valid"] is True, doc_val["errors"]
        assert doc_val["icm_form"] == expected_form

        audit = IcmAuditor().audit_workspace(mat_dir)
        assert audit.valid is True, audit.violations
        assert audit.invariants_passed == 10
        assert audit.form_detected == expected_form

        links = IcmVerifier().verify_links(mat_dir)
        assert links.valid is True, links.broken_links
        assert links.broken_links == []

        # 2.3(b) Portable dock entrypoints pass with bare `python` stripped from PATH
        empty_bin = tmp_path / "no_python_bin"
        empty_bin.mkdir(exist_ok=True)
        monkeypatch.setenv("PATH", str(empty_bin))

        res_val = runner.invoke(main, ["dock", "run", blueprint_name, "validate"])
        assert res_val.exit_code == 0, res_val.output
        assert "DOCK_HARNESS_OK" in res_val.output

        res_audit_docs = runner.invoke(main, ["dock", "run", blueprint_name, "audit-docs"])
        assert res_audit_docs.exit_code == 0, res_audit_docs.output
        assert "DOCS_AUDIT_OK" in res_audit_docs.output

        res_icm_audit = runner.invoke(main, ["dock", "run", blueprint_name, "icm-audit"])
        assert res_icm_audit.exit_code == 0, res_icm_audit.output
        assert "ICM_AUDIT_OK" in res_icm_audit.output

        res_icm_links = runner.invoke(main, ["dock", "run", blueprint_name, "icm-links"])
        assert res_icm_links.exit_code == 0, res_icm_links.output
        assert "ICM_LINKS_OK" in res_icm_links.output

        use_cases_text = (mat_dir / "docs" / "USE_CASES.md").read_text(encoding="utf-8")
        assert f"harness dock run {blueprint_name} audit-docs" in use_cases_text
        assert "harness dock run audit-docs" not in use_cases_text

    @pytest.mark.parametrize(
        "missing_rel",
        [
            "README.md",
            "CONTEXT.md",
            "docs/USE_CASES.md",
            "docs/PROVENANCE.md",
            "docs/RUNBOOK.md",
            ".agents/skills/icm-workspace-architect/CARD.md",
        ],
    )
    def test_validate_harness_docs_fails_when_required_artifact_deleted(
        self,
        tmp_path: Path,
        distiller_bundle: tuple[HarnessBlueprint, dict[str, str]],
        missing_rel: str,
    ) -> None:
        bp, tree = distiller_bundle
        mat_dir = tmp_path / "distiller"
        dock = DefaultDockService(workspace_root=tmp_path, state_file=tmp_path / "docks.json")
        materialize_spawn_as_dock(
            BRAIN_SURFACE,
            tree,
            mat_dir,
            name=bp.name,
            description=bp.mission,
            dock_service=dock,
            approve=True,
            blueprint=bp,
        )
        assert validate_harness_docs(mat_dir)["valid"] is True

        (mat_dir / missing_rel).unlink()
        failed = validate_harness_docs(mat_dir)
        assert failed["valid"] is False
        assert failed["errors"]

    @pytest.mark.parametrize(
        "tamper_rel",
        [
            "README.md",
            "CONTEXT.md",
            "docs/USE_CASES.md",
            "docs/PROVENANCE.md",
            "docs/RUNBOOK.md",
        ],
    )
    def test_check_drift_detects_documentation_tampering_and_restores_cleanly(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        security_bundle: tuple[HarnessBlueprint, dict[str, str]],
        tamper_rel: str,
    ) -> None:
        docks_state = tmp_path / "docks.json"
        monkeypatch.setenv("HARNESS_DOCKS_STATE_FILE", str(docks_state))
        bp, tree = security_bundle
        mat_dir = tmp_path / "sec"
        dock = DefaultDockService(workspace_root=tmp_path, state_file=docks_state)
        materialize_spawn_as_dock(
            BRAIN_SURFACE,
            tree,
            mat_dir,
            name=bp.name,
            description=bp.mission,
            dock_service=dock,
            approve=True,
            blueprint=bp,
        )

        runner = CliRunner()
        clean_drift = runner.invoke(main, ["spawn", "check-drift", str(mat_dir), "--dock-name", bp.name])
        assert clean_drift.exit_code == 0, clean_drift.output
        clean_payload = json.loads(clean_drift.output)
        assert clean_payload["drifted"] is False
        assert clean_payload["docs_drifted"] is False

        target = mat_dir / tamper_rel
        original = target.read_text(encoding="utf-8")
        target.write_text(original + "\n<!-- unauthorized edit -->\n", encoding="utf-8")

        tampered_drift = runner.invoke(main, ["spawn", "check-drift", str(mat_dir), "--dock-name", bp.name])
        assert tampered_drift.exit_code == 1
        tampered_payload = json.loads(tampered_drift.output)
        assert tampered_payload["docs_drifted"] is True
        assert tampered_payload["tree_drifted"] is False
        assert tampered_payload["drifted"] is True

        target.write_text(original, encoding="utf-8")
        restored_drift = runner.invoke(main, ["spawn", "check-drift", str(mat_dir), "--dock-name", bp.name])
        assert restored_drift.exit_code == 0, restored_drift.output
        assert json.loads(restored_drift.output)["drifted"] is False

    def test_broken_link_fails_audit_docs_entrypoint(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        distiller_bundle: tuple[HarnessBlueprint, dict[str, str]],
    ) -> None:
        docks_state = tmp_path / "docks.json"
        monkeypatch.setenv("HARNESS_DOCKS_STATE_FILE", str(docks_state))
        bp, tree = distiller_bundle
        mat_dir = tmp_path / "distiller_links"
        dock = DefaultDockService(workspace_root=tmp_path, state_file=docks_state)
        materialize_spawn_as_dock(
            BRAIN_SURFACE,
            tree,
            mat_dir,
            name=bp.name,
            description=bp.mission,
            dock_service=dock,
            approve=True,
            blueprint=bp,
        )

        readme = mat_dir / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\nSee [broken](missing_target.md)\n", encoding="utf-8")

        runner = CliRunner()
        res_bad = runner.invoke(main, ["dock", "run", bp.name, "audit-docs"])
        assert res_bad.exit_code != 0

    def test_standalone_cwd_dock_run_and_check_drift_without_env_override(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        distiller_bundle: tuple[HarnessBlueprint, dict[str, str]],
    ) -> None:
        monkeypatch.delenv("HARNESS_DOCKS_STATE_FILE", raising=False)
        prime_ws = tmp_path / "prime_ws"
        prime_ws.mkdir()
        mat_dir = tmp_path / "standalone_distiller"
        bp, tree = distiller_bundle

        monkeypatch.chdir(prime_ws)
        info = materialize_spawn_as_dock(
            BRAIN_SURFACE,
            tree,
            mat_dir,
            name=bp.name,
            description=bp.mission,
            approve=True,
            blueprint=bp,
        )
        assert info["approved"] is True
        assert (prime_ws / ".harness" / "docks.json").is_file()
        assert (mat_dir / ".harness" / "docks.json").is_file()

        monkeypatch.chdir(mat_dir)
        runner = CliRunner()
        res_val = runner.invoke(main, ["dock", "run", bp.name, "validate"])
        assert res_val.exit_code == 0, res_val.output
        assert "DOCK_HARNESS_OK" in res_val.output

        res_drift = runner.invoke(main, ["spawn", "check-drift", "."])
        assert res_drift.exit_code == 0, res_drift.output
        drift_data = json.loads(res_drift.output)
        assert drift_data["dock_status"] == "approved"
        assert drift_data["drifted"] is False

    def test_docs_sha256_is_reproducible_across_rematerializations(
        self,
        tmp_path: Path,
        distiller_bundle: tuple[HarnessBlueprint, dict[str, str]],
    ) -> None:
        bp, tree = distiller_bundle
        mat_a = tmp_path / "run_a"
        mat_b = tmp_path / "run_b"
        dock_a = DefaultDockService(workspace_root=tmp_path, state_file=tmp_path / "docks_a.json")
        dock_b = DefaultDockService(workspace_root=tmp_path, state_file=tmp_path / "docks_b.json")

        res_a1 = materialize_spawn_as_dock(
            BRAIN_SURFACE,
            tree,
            mat_a,
            name=bp.name,
            description=bp.mission,
            dock_service=dock_a,
            approve=True,
            blueprint=bp,
            prime_commit="deadbeef",
            spawn_id="spawn_fixed_id",
        )
        res_a2 = materialize_spawn_as_dock(
            BRAIN_SURFACE,
            tree,
            mat_a,
            name=bp.name,
            description=bp.mission,
            dock_service=dock_a,
            approve=True,
            blueprint=bp,
            prime_commit="deadbeef",
            spawn_id="spawn_fixed_id",
        )
        res_b = materialize_spawn_as_dock(
            BRAIN_SURFACE,
            tree,
            mat_b,
            name=bp.name,
            description=bp.mission,
            dock_service=dock_b,
            approve=True,
            blueprint=bp,
            prime_commit="deadbeef",
            spawn_id="spawn_fixed_id",
        )

        assert res_a1["docs_sha256"] == res_a2["docs_sha256"] == res_b["docs_sha256"]
        assert "Generated (UTC)" not in (mat_a / "README.md").read_text(encoding="utf-8")
        assert "Generated (UTC)" not in (mat_a / "docs" / "PROVENANCE.md").read_text(encoding="utf-8")

    def test_dock_run_portability_with_relative_pythonpath_env(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        distiller_bundle: tuple[HarnessBlueprint, dict[str, str]],
    ) -> None:
        bp, tree = distiller_bundle
        prime_root = Path.cwd().resolve()
        docks_state = tmp_path / "docks.json"
        mat_dir = tmp_path / "portable_distiller"
        dock = DefaultDockService(workspace_root=prime_root, state_file=docks_state)
        materialize_spawn_as_dock(
            BRAIN_SURFACE,
            tree,
            mat_dir,
            name=bp.name,
            description=bp.mission,
            dock_service=dock,
            approve=True,
            blueprint=bp,
        )

        monkeypatch.setenv("HARNESS_DOCKS_STATE_FILE", str(docks_state))
        monkeypatch.setenv("PYTHONPATH", f".{os.pathsep}src")
        scrubbed = _build_scrubbed_env(mat_dir)
        entries = scrubbed["PYTHONPATH"].split(os.pathsep)
        assert all(Path(e).is_absolute() for e in entries), entries
        assert entries[0] == str((mat_dir / "src").resolve())
        assert str((prime_root / "src").resolve()) in entries

        monkeypatch.chdir(mat_dir)
        runner = CliRunner()
        res_icm = runner.invoke(main, ["dock", "run", bp.name, "icm-audit"])
        assert res_icm.exit_code == 0, res_icm.output
        assert "ICM_AUDIT_OK" in res_icm.output

    def test_cold_walk_runner_and_cli_separates_automated_vs_human_points(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        security_bundle: tuple[HarnessBlueprint, dict[str, str]],
    ) -> None:
        docks_state = tmp_path / "docks.json"
        monkeypatch.setenv("HARNESS_DOCKS_STATE_FILE", str(docks_state))
        bp, tree = security_bundle
        mat_dir = tmp_path / "sec_walk"
        dock = DefaultDockService(workspace_root=tmp_path, state_file=docks_state)
        materialize_spawn_as_dock(
            BRAIN_SURFACE,
            tree,
            mat_dir,
            name=bp.name,
            description=bp.mission,
            dock_service=dock,
            approve=True,
            blueprint=bp,
        )

        report_auto = run_cold_walk(mat_dir, dock_name=bp.name)
        assert report_auto.automated_passed is True
        assert report_auto.human_points_verified is False
        assert report_auto.overall_passed is False
        assert len(report_auto.points) == 8
        assert report_auto.underlying_gates["icm_auditor_invariants"] == "10/10"
        by_num = {p.point_number: p for p in report_auto.points}
        assert by_num[1].status == "pending_human_judgment"
        assert by_num[5].status == "pending_human_judgment"
        assert by_num[8].status == "pending_human_judgment"
        assert all(by_num[n].status == "passed" for n in (2, 3, 4, 6, 7))

        runner = CliRunner()
        cli_ok = runner.invoke(main, ["spawn", "cold-walk", str(mat_dir), "--dock-name", bp.name, "--json"])
        assert cli_ok.exit_code == 0, cli_ok.output
        assert json.loads(cli_ok.output)["automated_passed"] is True

        cli_strict = runner.invoke(main, ["spawn", "cold-walk", str(mat_dir), "--dock-name", bp.name, "--strict"])
        assert cli_strict.exit_code == 1

        report_full = run_cold_walk(
            mat_dir,
            dock_name=bp.name,
            human_judgments={
                1: {"passed": True, "note": "Located scope in 2 reads"},
                5: {"passed": True, "note": "No duplicate canon"},
                8: {"passed": True, "note": "0 broken invariants"},
            },
            reader="test-reviewer",
        )
        assert report_full.overall_passed is True
        assert all(p.reader == "test-reviewer" for p in report_full.points if p.evaluation_mode == "human_judgment")
