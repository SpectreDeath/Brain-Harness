"""Unit tests covering edge cases and fixes from the Deep Audit of Plugin and Skill Creators."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.creator.creator import PluginCreator
from harness.creator.scaffold import ScaffoldResult
from harness.creator.skills import SkillResult, SkillScaffoldEngine, SkillValidator
from harness.creator.validator import (
    AstFunctionInspectionRule,
    RuleSeverity,
    ValidationContext,
    ValidationPipeline,
)
from harness.plugins.manifest import EntrypointSpec, PluginManifest


@pytest.mark.unit
class TestCreatorDeepAuditFixes:
    @pytest.mark.asyncio
    async def test_validation_pipeline_halts_on_fatal_failure(self, tmp_path: Path) -> None:
        """Verify pipeline halts immediately when a fatal check (like DirectoryExistenceRule) fails."""
        non_existent = tmp_path / "does_not_exist"
        pipeline = ValidationPipeline()
        report = await pipeline.execute(non_existent)

        assert report.valid is False
        # Only the directory check should have run
        assert len(report.checks) == 1
        assert report.checks[0].name == "Directory Existence"
        assert report.checks[0].passed is False

    @pytest.mark.asyncio
    async def test_validation_pipeline_halts_on_missing_manifest(self, tmp_path: Path) -> None:
        """Verify pipeline halts on missing manifest and does not execute downstream AST rules."""
        empty_dir = tmp_path / "empty_plugin"
        empty_dir.mkdir()

        pipeline = ValidationPipeline()
        report = await pipeline.execute(empty_dir, remediate=False)

        assert report.valid is False
        # Should have Directory Existence (pass) and Manifest Schema (fail), but NOT entrypoint/AST checks
        check_names = [c.name for c in report.checks]
        assert "Directory Existence" in check_names
        assert "Manifest Schema" in check_names
        assert "Entrypoint File" not in check_names
        assert "AST Function Inspection" not in check_names

    @pytest.mark.asyncio
    async def test_remediation_typing_import_detection_with_docstrings(self, tmp_path: Path) -> None:
        """Verify that words like 'Any' or 'typing' in comments or docstrings do not fool import detection."""
        target = tmp_path / "test_docstring_plugin"
        target.mkdir()

        manifest = PluginManifest(
            name="test_doc",
            version="0.1.0",
            description="Test",
            language="python",
            entrypoint="main.py",
            entrypoints=[EntrypointSpec(name="missing_handler", description="Needs remediation")],
        )
        (target / "plugin.json").write_text(manifest.model_dump_json(), encoding="utf-8")

        # Code contains 'Any' in a docstring, but has NO typing import
        initial_code = '"""Any task can be run here without typing."""\n\ndef other():\n    pass\n'
        (target / "main.py").write_text(initial_code, encoding="utf-8")

        rule = AstFunctionInspectionRule()
        ctx = ValidationContext(path=target, remediate=True)
        ctx.manifest = manifest

        res = await rule.validate(ctx)
        assert res is True
        assert ctx.report.valid is True

        remediated_code = (target / "main.py").read_text(encoding="utf-8")
        assert "from typing import Any" in remediated_code
        assert "def missing_handler(" in remediated_code

    def test_container_archetype_typescript_dockerfile(self, tmp_path: Path) -> None:
        """Verify ContainerArchetype generates tsx entrypoint and tsconfig in Dockerfile for TypeScript."""
        target = tmp_path / "ts_container"
        _ = PluginCreator.scaffold(
            target,
            name="ts-container",
            preset="container",
            language="typescript",
            auto_validate=True,
        )

        dockerfile = (target / "Dockerfile").read_text(encoding="utf-8")
        assert "tsx" in dockerfile
        assert "tsconfig.json" in dockerfile
        assert 'ENTRYPOINT ["npx", "tsx", "index.ts"]' in dockerfile

    def test_scaffold_result_to_dict_typing(self, tmp_path: Path) -> None:
        """Verify ScaffoldResult.to_dict handles typed validation reports without hasattr duck-typing."""
        manifest = PluginManifest(name="test_dict", version="0.1.0", language="python")
        sr_none = ScaffoldResult(path=tmp_path, manifest=manifest)
        d_none = sr_none.to_dict()
        assert d_none["validation_report"] is None

        sr_valid = PluginCreator.scaffold(
            tmp_path / "valid_proj",
            name="valid-proj",
            auto_validate=True,
        )
        d_valid = sr_valid.to_dict()
        assert d_valid["validation_report"] is not None
        assert d_valid["validation_report"]["valid"] is True

    @pytest.mark.asyncio
    async def test_skill_scaffold_async_runs_in_thread(self, tmp_path: Path) -> None:
        """Verify SkillScaffoldEngine.scaffold_async executes cleanly in asyncio context."""
        target = tmp_path / "async_skill_audit"
        res = await SkillScaffoldEngine.scaffold_async(
            target,
            name="async-audit-skill",
            description="Audit async scaffolding.",
            auto_validate=True,
        )
        assert isinstance(res, SkillResult)
        assert res.skill_file.exists()
        assert res.validation_report is not None
        assert res.validation_report.valid is True

    def test_skill_validator_missing_pillars_records_failed_checks(self, tmp_path: Path) -> None:
        """Verify missing pillars in SKILL.md record advisory warning checks (severity WARNING)."""
        target = tmp_path / "bare_skill"
        target.mkdir()

        # SKILL.md without Visual Brief, Checkpoint, or Anti-Patterns
        bare_skill_text = (
            "---\n"
            "name: bare-skill\n"
            "description: A bare skill without pillars.\n"
            "---\n\n"
            "# Bare Skill\n\n"
            "Just simple text.\n"
        )
        (target / "SKILL.md").write_text(bare_skill_text, encoding="utf-8")

        report = SkillValidator.validate(target)
        # Missing pillars are warnings, so report is still valid (not fatal), checks record WARNING severity
        assert report.valid is True
        pillar_checks = [c for c in report.checks if c.name in ("Visual Brief Pillar", "Mandatory Checkpoint", "Anti-Patterns", "CARD.md Summary")]
        assert len(pillar_checks) == 4
        for c in pillar_checks:
            assert c.passed is True
            assert c.severity == RuleSeverity.WARNING

    def test_skill_validator_line_anchored_frontmatter(self, tmp_path: Path) -> None:
        """Verify frontmatter validation rejects inline substrings disguised as fields."""
        target = tmp_path / "invalid_fm_skill"
        target.mkdir()

        # Frontmatter where 'name' and 'description' are only part of a comment or unanchored text
        bad_fm_text = (
            "---\n"
            "# This mentions name: foo in a comment\n"
            "foo_description: bar\n"
            "---\n\n"
            "# Bad Skill\n"
        )
        (target / "SKILL.md").write_text(bad_fm_text, encoding="utf-8")

        report = SkillValidator.validate(target)
        assert report.valid is False
        assert any("Frontmatter must contain 'name' and 'description'" in err for err in report.errors)

    def test_compile_dynamic_module_syntax_error_prevalidation(self) -> None:
        """Verify _compile_dynamic_module raises ValueError with line number on SyntaxError."""
        from harness.creator.dynamic import _compile_dynamic_module

        bad_code = "def broken(\n   this is not valid python syntax"
        with pytest.raises(ValueError, match=r"Syntax error in dynamic plugin 'bad_syntax'"):
            _compile_dynamic_module("bad_syntax", bad_code)

    def test_compile_dynamic_module_runtime_error(self) -> None:
        """Verify _compile_dynamic_module raises RuntimeError on module-level execution errors."""
        from harness.creator.dynamic import _compile_dynamic_module

        exec_error_code = "undefined_variable.some_method()"
        with pytest.raises(RuntimeError, match=r"Execution error in dynamic plugin 'exec_err'"):
            _compile_dynamic_module("exec_err", exec_error_code)

    def test_archetype_registry_snapshot_isolation(self) -> None:
        """Verify ArchetypeRegistry.snapshot() preserves state and prevents test pollution."""
        from harness.creator.archetypes import ArchetypeRegistry, GeneralArchetype

        class CustomTempArchetype(GeneralArchetype):
            @property
            def name(self) -> str:
                return "temporary_test_arch"

        assert not ArchetypeRegistry.has("temporary_test_arch")

        with ArchetypeRegistry.snapshot():
            ArchetypeRegistry.register(CustomTempArchetype())
            assert ArchetypeRegistry.has("temporary_test_arch")
            assert ArchetypeRegistry.get("temporary_test_arch").name == "temporary_test_arch"

        # After snapshot context exits, state is fully restored
        assert not ArchetypeRegistry.has("temporary_test_arch")
