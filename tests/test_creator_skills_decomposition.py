"""Characterization test contract for Creator Skills decomposed package architecture.

Verifies:
1. Submodule independence and public facade parity.
2. Slotted dataclass architecture for SkillOptions and SkillResult (Rule 12).
3. PathLike protocol conformance for SkillResult (fspath, division operator).
4. Diagnostic interface invariant: report.valid evaluation and granular checks (Rule 34).
5. Synchronous and coroutine dual-mode invocation contract (Rule 38).
6. Single-seam resolver seam (Rule 58).
7. Skill scaffolding and craft standard rule verification.
"""

from __future__ import annotations

import os
from pathlib import Path
import pytest


@pytest.mark.unit
class TestCreatorSkillsDecompositionParity:
    """Verifies submodule isolation, public export parity, and slotted contracts."""

    def test_submodule_import_isolation(self) -> None:
        """Verify each submodule can be imported independently without circular dependencies."""
        from harness.creator.skills import models, rules, scaffold, validator

        assert hasattr(models, "SkillOptions")
        assert hasattr(models, "SkillResult")

        assert hasattr(rules, "SkillDirectoryRule")
        assert hasattr(rules, "SkillFrontmatterRule")
        assert hasattr(rules, "SkillPillarRule")
        assert hasattr(rules, "SkillCardRule")

        assert hasattr(scaffold, "SkillScaffoldEngine")

        assert hasattr(validator, "SkillValidator")
        assert hasattr(validator, "resolve_skill_validator")

    def test_facade_all_symbol_export_parity(self) -> None:
        """Verify the facade in __init__.py exports all 8 original symbols."""
        import harness.creator.skills as skills_pkg

        expected_symbols = [
            "SkillCardRule",
            "SkillDirectoryRule",
            "SkillFrontmatterRule",
            "SkillOptions",
            "SkillPillarRule",
            "SkillResult",
            "SkillScaffoldEngine",
            "SkillValidator",
        ]
        for sym in expected_symbols:
            assert hasattr(skills_pkg, sym), f"Facade missing original symbol: {sym}"
            assert sym in skills_pkg.__all__, f"__all__ missing symbol: {sym}"

    def test_slotted_dataclass_architecture(self, tmp_path: Path) -> None:
        """Verify slotted dataclasses minimize memory footprint (Rule 12)."""
        from harness.creator.skills.models import SkillOptions, SkillResult

        assert hasattr(SkillOptions, "__slots__")
        assert hasattr(SkillResult, "__slots__")

        opts = SkillOptions(name="test-skill")
        assert opts.name == "test-skill"
        assert opts.include_card is True

        res = SkillResult(
            path=tmp_path,
            skill_file=tmp_path / "SKILL.md",
            card_file=tmp_path / "CARD.md",
            generated_files=[tmp_path / "SKILL.md", tmp_path / "CARD.md"],
        )
        assert res.files_count == 2
        assert os.fspath(res) == str(tmp_path)
        assert str(res) == str(tmp_path)
        assert (res / "extra.txt") == (tmp_path / "extra.txt")

        res_dict = res.to_dict()
        assert res_dict["path"] == str(tmp_path)
        assert res_dict["files_count"] == 2

    def test_diagnostic_report_interface_invariant_rule_34(self, tmp_path: Path) -> None:
        """Verify Rule 34: SkillValidator produces ValidationReport with .valid, not .passed."""
        from harness.creator.skills.validator import SkillValidator

        # Test on empty dir (fails directory/skill check)
        empty_dir = tmp_path / "empty_dir"
        empty_dir.mkdir()

        report = SkillValidator.validate(empty_dir)
        assert hasattr(report, "valid")
        assert isinstance(report.valid, bool)
        assert not hasattr(report, "passed")
        assert report.valid is False
        assert len(report.errors) > 0
        assert any(c.name == "SKILL.md File" and not c.passed for c in report.checks)


@pytest.mark.unit
class TestCreatorSkillsEngineAndValidator:
    """Verifies scaffolding engine, dual-mode invocation, and resolver seam."""

    def test_scaffold_sync_and_rules(self, tmp_path: Path) -> None:
        """Verify synchronous scaffolding and rule verification."""
        from harness.creator.skills.models import SkillOptions
        from harness.creator.skills.scaffold import SkillScaffoldEngine
        from harness.creator.skills.validator import SkillValidator

        target = tmp_path / "sync_skill"
        opts = SkillOptions(
            name="deep-refactor",
            description="Execute deep refactoring loops.",
            category="architecture",
            triggers=["refactor", "deepen"],
            auto_validate=True,
        )

        res = SkillScaffoldEngine.scaffold(target, options=opts)
        assert res.skill_file.exists()
        assert res.card_file is not None and res.card_file.exists()
        assert res.validation_report is not None
        assert res.validation_report.valid is True

        # Re-validate via SkillValidator
        report = SkillValidator.validate_sync(target)
        assert report.valid is True
        assert any(c.name == "Skill Directory" and c.passed for c in report.checks)
        assert any(c.name in ("SKILL.md File", "YAML Frontmatter") and c.passed for c in report.checks)
        assert any(c.name in ("Skill Pillars", "Visual Brief Pillar") and c.passed for c in report.checks)
        assert any(c.name == "CARD.md Summary" and c.passed for c in report.checks)

    @pytest.mark.asyncio
    async def test_scaffold_async_and_validate_async(self, tmp_path: Path) -> None:
        """Verify coroutine scaffolding and async validation (Rule 38)."""
        from harness.creator.skills.scaffold import SkillScaffoldEngine
        from harness.creator.skills.validator import SkillValidator

        target = tmp_path / "async_skill"
        res = await SkillScaffoldEngine.scaffold_async(
            target,
            name="async-builder",
            description="Async builder skill.",
            auto_validate=True,
        )
        assert res.skill_file.exists()
        assert res.validation_report is not None
        assert res.validation_report.valid is True

        # Validate asynchronously
        report = await SkillValidator.validate_async(target)
        assert report.valid is True

    def test_single_seam_resolver(self) -> None:
        """Verify single-seam resolver function (Rule 58)."""
        from harness.creator.skills.validator import (
            SkillValidator,
            resolve_skill_validator,
        )

        validator = resolve_skill_validator(None)
        assert validator is SkillValidator or isinstance(validator, SkillValidator)
