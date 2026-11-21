"""Contract and portability tests for 7-part harness docs & drift digest (Track 2.3)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from click.testing import CliRunner
import pytest

from harness.cli import main
from harness.services.dock import DefaultDockService
from harness.services.harness_spawner import (
    HarnessBlueprint,
    build_blueprint_tree,
    materialize_spawn_as_dock,
    recommend_harness_blueprints,
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
