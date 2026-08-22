"""Comprehensive unit tests for deepened creator & skill pipeline architecture."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from harness.creator.dynamic import _compile_dynamic_module
from harness.creator.scaffold import ScaffoldOptions
from harness.creator.skills import (
    SkillFrontmatterRule,
    SkillOptions,
    SkillScaffoldEngine,
    SkillValidator,
)
from harness.creator.validator import (
    AstFunctionInspectionRule,
    RuleSeverity,
    ValidationContext,
    _run_coro_sync,
)
from harness.plugins.manifest import EntrypointSpec, PluginManifest


@pytest.mark.unit
class TestDeepenedCreatorSkillPipeline:
    def test_scaffold_options_from_kwargs_factory(self, tmp_path: Path) -> None:
        """Verify ScaffoldOptions.from_kwargs properly merges defaults and overrides."""
        target = tmp_path / "custom_named_plugin"
        opts = ScaffoldOptions.from_kwargs(
            target_dir=target,
            description="Custom plugin description",
            language="python",
            tools=["custom_tool"],
            preset="service",
        )
        assert opts.name == "custom_named_plugin"
        assert opts.description == "Custom plugin description"
        assert opts.language == "python"
        assert opts.tools == ["custom_tool"]
        assert opts.preset == "service"

        # Pre-existing instance should pass through untouched
        existing = ScaffoldOptions(name="passed_directly")
        merged = ScaffoldOptions.from_kwargs(options=existing, name="ignored")
        assert merged is existing
        assert merged.name == "passed_directly"

    def test_compile_dynamic_module(self) -> None:
        """Verify _compile_dynamic_module compiles source and extracts callables."""
        code = """
def compute_sum(a: int, b: int) -> int:
    return a + b

def _private_helper():
    return None

CONSTANT_VAL = 42
"""
        mod, tools = _compile_dynamic_module("calculator", code)
        assert "compute_sum" in tools
        assert "_private_helper" not in tools
        assert "CONSTANT_VAL" not in tools
        assert callable(tools["compute_sum"])
        assert tools["compute_sum"](10, 32) == 42

    @pytest.mark.asyncio
    async def test_remediation_typing_import_placement_after_docstring(self, tmp_path: Path) -> None:
        """Verify that AstFunctionInspectionRule inserts typing import AFTER module docstring."""
        target = tmp_path / "docstring_placement_plugin"
        target.mkdir()

        manifest = PluginManifest(
            name="docstring_test",
            version="0.1.0",
            language="python",
            entrypoint="main.py",
            entrypoints=[EntrypointSpec(name="process_item", description="Item processor")],
        )
        (target / "plugin.json").write_text(manifest.model_dump_json(), encoding="utf-8")

        initial_source = '"""Module docstring that must stay at the very top of the file."""\n\ndef existing_func():\n    pass\n'
        (target / "main.py").write_text(initial_source, encoding="utf-8")

        rule = AstFunctionInspectionRule()
        ctx = ValidationContext(path=target, remediate=True)
        ctx.manifest = manifest

        res = await rule.validate(ctx)
        assert res is True

        remediated_source = (target / "main.py").read_text(encoding="utf-8")
        lines = remediated_source.splitlines()

        # Line 0 must still be the docstring
        assert lines[0].startswith('"""Module docstring')
        # from typing import Any must be after docstring
        assert "from typing import Any" in remediated_source
        assert remediated_source.index('"""Module docstring') < remediated_source.index("from typing import Any")
        assert "def process_item(" in remediated_source

    @pytest.mark.asyncio
    async def test_add_warn_sets_passed_true_with_warning_severity(self, tmp_path: Path) -> None:
        """Verify ValidationContext.add_warn marks check.passed=True with RuleSeverity.WARNING."""
        ctx = ValidationContext(path=tmp_path)
        ctx.add_warn("Test Warning Check", "This is an architectural warning")

        assert ctx.report.valid is True  # Report remains overall valid
        assert len(ctx.report.warnings) == 1
        assert ctx.report.warnings[0] == "This is an architectural warning"

        check = ctx.report.checks[0]
        assert check.name == "Test Warning Check"
        assert check.passed is True
        assert check.severity == RuleSeverity.WARNING
        assert "Warning:" in check.message

    def test_run_coro_sync_safe_inside_running_loop(self) -> None:
        """Verify _run_coro_sync executes successfully even if called within an active loop."""
        async def dummy_async_work(val: int) -> int:
            await asyncio.sleep(0.01)
            return val * 2

        # Test top-level sync call
        result = _run_coro_sync(dummy_async_work(21))
        assert result == 42

        # Test nested call from inside an active asyncio loop
        async def run_nested_sync() -> int:
            return _run_coro_sync(dummy_async_work(50))

        nested_res = asyncio.run(run_nested_sync())
        assert nested_res == 100

    @pytest.mark.asyncio
    async def test_skill_validator_pipeline_rules_isolation(self, tmp_path: Path) -> None:
        """Test individual SkillValidation rules through composable ValidationPipeline."""
        skill_dir = tmp_path / "pipeline_test_skill"
        skill_dir.mkdir()

        # 1. Test missing SKILL.md fails frontmatter rule
        ctx = ValidationContext(path=skill_dir)
        fm_rule = SkillFrontmatterRule()
        assert await fm_rule.validate(ctx) is False
        assert ctx.report.valid is False

        # 2. Write valid SKILL.md
        opts = SkillOptions(
            name="pipeline-skill",
            description="Testing pipeline rules.",
            triggers=["/pipeline-skill"],
        )
        (skill_dir / "SKILL.md").write_text(SkillScaffoldEngine.generate_skill_md(opts), encoding="utf-8")
        (skill_dir / "CARD.md").write_text(SkillScaffoldEngine.generate_card_md(opts), encoding="utf-8")

        # 3. Test full pipeline execution
        report = await SkillValidator.validate_async(skill_dir)
        assert report.valid is True
        assert len(report.errors) == 0
        assert len(report.checks) >= 4
        assert any(c.name == "Skill Directory" and c.passed for c in report.checks)
        assert any(c.name == "YAML Frontmatter" and c.passed for c in report.checks)
        assert any(c.name == "Visual Brief Pillar" and c.passed for c in report.checks)
        assert any(c.name == "CARD.md Summary" and c.passed for c in report.checks)

    def test_skill_validator_sync_helpers(self, tmp_path: Path) -> None:
        """Verify SkillValidator sync helpers function cleanly."""
        skill_dir = tmp_path / "sync_skill_test"
        SkillScaffoldEngine.scaffold(skill_dir, name="sync-skill", description="Testing sync helpers.")

        report = SkillValidator.validate_sync(skill_dir)
        assert report.valid is True
        assert len(report.checks) >= 4
