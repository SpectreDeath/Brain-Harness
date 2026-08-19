"""Tests for PluginValidator and pre-flight validation checks."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from harness.cli import main
from harness.creator.scaffold import PluginScaffoldEngine, ScaffoldOptions
from harness.creator.validator import PluginValidator


@pytest.mark.unit
@pytest.mark.asyncio
class TestPluginValidator:
    async def test_validate_valid_scaffolded_plugin(self, tmp_path: Path) -> None:
        target = tmp_path / "valid_plugin"
        engine = PluginScaffoldEngine()
        engine.scaffold(
            target,
            options=ScaffoldOptions(
                name="valid-plugin",
                description="Valid plugin for test",
                language="python",
                tools=["execute", "process"],
            ),
        )

        report = await PluginValidator.validate(target, dry_run=False)
        assert report.valid is True
        assert len(report.errors) == 0
        assert any(c.name == "Manifest Schema" and c.passed for c in report.checks)
        assert any(c.name == "AST Function Inspection" and c.passed for c in report.checks)

    async def test_validate_missing_directory(self, tmp_path: Path) -> None:
        missing = tmp_path / "non_existent"
        report = await PluginValidator.validate(missing)
        assert report.valid is False
        assert any("does not exist" in err for err in report.errors)

    async def test_validate_missing_manifest(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "empty_plugin"
        empty_dir.mkdir()
        report = await PluginValidator.validate(empty_dir)
        assert report.valid is False
        assert any("Missing plugin.json" in err for err in report.errors)

    async def test_validate_corrupt_manifest_schema(self, tmp_path: Path) -> None:
        bad_dir = tmp_path / "bad_manifest"
        bad_dir.mkdir()
        (bad_dir / "plugin.json").write_text("{corrupt json", encoding="utf-8")
        report = await PluginValidator.validate(bad_dir)
        assert report.valid is False
        assert any("Failed to parse plugin.json" in err for err in report.errors)

    async def test_validate_missing_entrypoint_file(self, tmp_path: Path) -> None:
        no_entry_dir = tmp_path / "no_entry"
        no_entry_dir.mkdir()
        manifest_data = {
            "name": "no-entry-plugin",
            "version": "0.1.0",
            "language": "python",
            "entrypoint": "main.py",
        }
        (no_entry_dir / "plugin.json").write_text(json.dumps(manifest_data), encoding="utf-8")

        report = await PluginValidator.validate(no_entry_dir)
        assert report.valid is False
        assert any("Entrypoint file 'main.py' not found" in err for err in report.errors)

    async def test_validate_ast_missing_functions(self, tmp_path: Path) -> None:
        mismatch_dir = tmp_path / "mismatch_plugin"
        mismatch_dir.mkdir()
        manifest_data = {
            "name": "mismatch-plugin",
            "version": "0.1.0",
            "language": "python",
            "entrypoint": "main.py",
            "entrypoints": [
                {"name": "func_alpha", "parameters": []},
                {"name": "func_missing", "parameters": []},
            ],
        }
        (mismatch_dir / "plugin.json").write_text(json.dumps(manifest_data), encoding="utf-8")
        (mismatch_dir / "main.py").write_text("def func_alpha(): pass\n", encoding="utf-8")

        report = await PluginValidator.validate(mismatch_dir)
        assert report.valid is False
        assert any("missing in main.py: ['func_missing']" in err for err in report.errors)

    async def test_validate_dry_run_sandbox_success(self, tmp_path: Path) -> None:
        target = tmp_path / "dry_run_plugin"
        engine = PluginScaffoldEngine()
        engine.scaffold(
            target,
            options=ScaffoldOptions(
                name="dry-run-plugin",
                language="python",
                tools=["sample_calc"],
            ),
        )

        report = await PluginValidator.validate(target, dry_run=True)
        assert report.valid is True
        assert any(c.name == "Sandbox Dry-Run" and c.passed for c in report.checks)


@pytest.mark.unit
def test_cli_creator_validate_command(tmp_path: Path) -> None:
    target = tmp_path / "cli_valid"
    engine = PluginScaffoldEngine()
    engine.scaffold(target, name="cli-valid", language="python", tools=["execute"])

    runner = CliRunner()
    result = runner.invoke(main, ["creator", "validate", str(target), "--dry-run"])
    assert result.exit_code == 0
    assert "Overall Status: ✓ PASS" in result.output
