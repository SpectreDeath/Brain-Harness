"""Unit and integration tests for authoritative PluginCreator facade and rules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from harness.cli import main
from harness.creator.creator import PluginCreator
from harness.creator.scaffold import ScaffoldOptions, ScaffoldResult
from harness.creator.validator import PluginValidator, RuleSeverity


@pytest.mark.unit
class TestPluginCreatorFacade:
    def test_scaffold_sync_and_result(self, tmp_path: Path) -> None:
        target = tmp_path / "creator_sync_test"
        res = PluginCreator.scaffold(
            target,
            name="creator-sync",
            preset="tool",
            language="python",
            tools=["analyze_data", "clean_data"],
            dependencies=["numpy>=1.26.0"],
        )

        assert isinstance(res, ScaffoldResult)
        assert res.path == target
        assert (target / "plugin.json").exists()
        assert (target / "main.py").exists()
        assert (target / "requirements.txt").exists()
        assert "numpy>=1.26.0" in (target / "requirements.txt").read_text(encoding="utf-8")

    @pytest.mark.asyncio
    async def test_scaffold_async(self, tmp_path: Path) -> None:
        target = tmp_path / "creator_async_test"
        res = await PluginCreator.scaffold_async(
            target,
            name="creator-async",
            preset="agentic_workflow",
            auto_validate=True,
        )

        assert isinstance(res, ScaffoldResult)
        assert res.validation_report is not None
        assert res.validation_report.valid is True
        assert (target / "README.md").exists()

    def test_from_functions_and_infer_manifest(self) -> None:
        def process_text(text: str, max_chars: int = 100) -> str:
            """Shorten text to max chars."""
            return text[:max_chars]

        plugin = PluginCreator.from_functions(
            name="text-processor",
            functions=[process_text],
            description="Process and truncate text",
        )
        assert plugin.name == "text-processor"
        assert "process_text" in plugin.tools

        manifest = plugin.infer_manifest()
        assert manifest.name == "text-processor"
        assert len(manifest.entrypoints) == 1
        assert manifest.entrypoints[0].name == "process_text"

    def test_from_code(self) -> None:
        code = """
def multiplier(val: int, factor: int = 2) -> int:
    return val * factor
"""
        plugin = PluginCreator.from_code("dynamic-mult", code)
        assert plugin.name == "dynamic-mult"
        assert "multiplier" in plugin.tools

    def test_list_and_get_archetypes(self) -> None:
        archetypes = PluginCreator.list_archetypes()
        assert len(archetypes) >= 7
        names = [a["name"] for a in archetypes]
        assert "general" in names
        assert "agentic_workflow" in names
        assert "container" in names

        arch = PluginCreator.get_archetype("agentic_workflow")
        assert arch.name == "agentic_workflow"

    @pytest.mark.asyncio
    async def test_validate_and_remediate(self, tmp_path: Path) -> None:
        target = tmp_path / "broken_plugin_to_fix"
        target.mkdir()

        # Missing manifest
        report = await PluginCreator.validate(target)
        assert report.valid is False

        # Run auto-remediation
        fix_report = await PluginCreator.remediate(target)
        assert fix_report.valid is True
        assert (target / "plugin.json").exists()
        assert (target / "main.py").exists()

    @pytest.mark.asyncio
    async def test_javascript_static_analysis_rule(self, tmp_path: Path) -> None:
        target = tmp_path / "js_plugin"
        target.mkdir()

        manifest_data = {
            "name": "js-sample",
            "version": "0.1.0",
            "language": "javascript",
            "entrypoint": "index.js",
            "entrypoints": [
                {"name": "fetchData", "parameters": []},
                {"name": "missingHandler", "parameters": []},
            ],
        }
        (target / "plugin.json").write_text(json.dumps(manifest_data), encoding="utf-8")
        (target / "index.js").write_text("export function fetchData() { return { status: 'ok' }; }\n", encoding="utf-8")

        # Initial validation should detect missing export
        report = await PluginCreator.validate(target)
        assert report.valid is False
        assert any("missing in index.js: ['missingHandler']" in err for err in report.errors)

        # Auto-remediation should append export stub
        fixed_report = await PluginCreator.remediate(target)
        assert fixed_report.valid is True
        assert "export async function missingHandler" in (target / "index.js").read_text(encoding="utf-8")

    @pytest.mark.asyncio
    async def test_dependency_manifest_rule_and_remediation(self, tmp_path: Path) -> None:
        target = tmp_path / "dep_plugin"
        target.mkdir()

        manifest_data = {
            "name": "dep-sample",
            "version": "0.1.0",
            "language": "python",
            "entrypoint": "main.py",
            "entrypoints": [{"name": "execute", "parameters": []}],
            "dependencies": ["requests>=2.31.0", "pydantic>=2.0.0"],
        }
        (target / "plugin.json").write_text(json.dumps(manifest_data), encoding="utf-8")
        (target / "main.py").write_text("def execute(): return {'status': 'ok'}\n", encoding="utf-8")
        (target / "requirements.txt").write_text("requests>=2.31.0\n", encoding="utf-8")

        # Should warn or fail on missing pydantic in requirements.txt
        report = await PluginCreator.validate(target)
        assert any("pydantic" in warn for warn in report.warnings)

        # Auto-remediate should append pydantic to requirements.txt
        fixed_report = await PluginCreator.remediate(target)
        req_text = (target / "requirements.txt").read_text(encoding="utf-8")
        assert "pydantic>=2.0.0" in req_text


@pytest.mark.unit
def test_cli_creator_commands(tmp_path: Path) -> None:
    runner = CliRunner()

    # 1. Test archetypes command
    res_arch = runner.invoke(main, ["creator", "archetypes"])
    assert res_arch.exit_code == 0
    assert "Available Plugin Archetypes" in res_arch.output
    assert "agentic_workflow" in res_arch.output

    # 2. Test scaffold command
    target_dir = tmp_path / "cli_scaffold_test"
    res_scaffold = runner.invoke(
        main,
        ["creator", "scaffold", "cli-test", "--preset", "tool", "--target-dir", str(target_dir)],
    )
    assert res_scaffold.exit_code == 0
    assert (target_dir / "plugin.json").exists()

    # 3. Test validate command with --fix flag
    res_validate = runner.invoke(main, ["creator", "validate", str(target_dir), "--fix"])
    assert res_validate.exit_code == 0
    assert "PASS" in res_validate.output
