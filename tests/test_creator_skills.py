"""Unit tests for SkillCreator and SkillValidator."""

from __future__ import annotations

from pathlib import Path
import pytest
from click.testing import CliRunner

from harness.cli import main
from harness.creator.creator import PluginCreator
from harness.creator.skills import SkillOptions, SkillResult, SkillScaffoldEngine, SkillValidator


@pytest.mark.unit
class TestSkillCreatorAndValidator:
    def test_scaffold_skill_sync(self, tmp_path: Path) -> None:
        target = tmp_path / "test_skill"
        opts = SkillOptions(
            name="memory-profiler",
            description="Profile and optimize agent memory usage. Use when triggered by 'memory leak' or 'profile memory'.",
            category="profiling / memory",
            triggers=["memory leak", "profile memory", "/memory-profiler"],
            auto_validate=True,
        )
        res = SkillScaffoldEngine.scaffold(target, options=opts)

        assert isinstance(res, SkillResult)
        assert res.path == target
        assert (target / "SKILL.md").exists()
        assert (target / "CARD.md").exists()
        assert (target / "README.md").exists()
        assert res.validation_report is not None
        assert res.validation_report.valid is True

        skill_text = (target / "SKILL.md").read_text(encoding="utf-8")
        assert "name: memory-profiler" in skill_text
        assert "The Visual Brief" in skill_text
        assert "Mandatory Checkpoint" in skill_text
        assert "Behavioral Guardrails" in skill_text

        card_text = (target / "CARD.md").read_text(encoding="utf-8")
        assert "SKILL: memory-profiler" in card_text
        assert "Stage Progression Table" in card_text

    @pytest.mark.asyncio
    async def test_scaffold_skill_async(self, tmp_path: Path) -> None:
        target = tmp_path / "async_skill"
        res = await SkillScaffoldEngine.scaffold_async(
            target,
            name="async-architect",
            description="Architect async loops.",
            auto_validate=True,
        )

        assert res.validation_report is not None
        assert res.validation_report.valid is True

    def test_plugin_creator_facade_skill_methods(self, tmp_path: Path) -> None:
        target = tmp_path / "facade_skill"
        res = PluginCreator.scaffold_skill(
            target,
            name="facade-skill",
            description="Test skill from facade.",
            auto_validate=True,
        )
        assert res.skill_file.exists()

        report = PluginCreator.validate_skill(target)
        assert report.valid is True

    def test_skill_validator_missing_files(self, tmp_path: Path) -> None:
        target = tmp_path / "invalid_skill"
        target.mkdir()

        report = SkillValidator.validate(target)
        assert report.valid is False
        assert any("Missing SKILL.md" in err for err in report.errors)

    def test_cli_skills_create_and_validate(self, tmp_path: Path) -> None:
        runner = CliRunner()
        target = tmp_path / "cli_created_skill"

        create_res = runner.invoke(
            main,
            [
                "skills",
                "create",
                "cli-auditor",
                "--description",
                "Audit system invariants.",
                "--category",
                "epistemic-governance",
                "--target-dir",
                str(target),
                "--validate",
            ],
        )
        assert create_res.exit_code == 0
        assert "Scaffolded agent skill 'cli-auditor'" in create_res.output
        assert (target / "SKILL.md").exists()
        assert (target / "CARD.md").exists()

        validate_res = runner.invoke(main, ["skills", "validate", str(target)])
        assert validate_res.exit_code == 0
        assert "Overall Status: ✓ PASS" in validate_res.output
