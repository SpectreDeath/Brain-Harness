"""Diagnostic validator verifying agent skills against craft standards."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from harness.creator.skills.rules import (
    SkillCardRule,
    SkillDirectoryRule,
    SkillFrontmatterRule,
    SkillPillarRule,
)
from harness.creator.validator import (
    ValidationPipeline,
    ValidationReport,
    _run_coro_sync,
)


class SkillValidator:
    """Diagnostic validator verifying agent skills against craft standards."""

    @classmethod
    def default_pipeline(cls) -> ValidationPipeline:
        """Create a default ValidationPipeline with all skill craft rules."""
        return ValidationPipeline(
            rules=[
                SkillDirectoryRule(),
                SkillFrontmatterRule(),
                SkillPillarRule(),
                SkillCardRule(),
            ]
        )

    @classmethod
    async def validate_async(
        cls,
        skill_dir: Path | str,
        *,
        pipeline: ValidationPipeline | None = None,
    ) -> ValidationReport:
        """Asynchronously validate an agent skill directory."""
        active_pipeline = pipeline or cls.default_pipeline()
        return await active_pipeline.execute(skill_dir)

    @classmethod
    def validate(
        cls,
        skill_dir: Path | str,
        *,
        pipeline: ValidationPipeline | None = None,
    ) -> ValidationReport:
        """Validate an agent skill directory."""
        return cast(ValidationReport, _run_coro_sync(cls.validate_async(skill_dir, pipeline=pipeline)))

    @classmethod
    def validate_sync(
        cls,
        skill_dir: Path | str,
        *,
        pipeline: ValidationPipeline | None = None,
    ) -> ValidationReport:
        """Synchronously validate an agent skill directory."""
        return cls.validate(skill_dir, pipeline=pipeline)


def resolve_skill_validator(context: Any = None) -> type[SkillValidator] | SkillValidator:
    """Single-seam resolver for SkillValidator service (Rule 58).

    Resolves configured validator from IoC container if available, otherwise
    falls back to the authoritative SkillValidator class.
    """
    if context is not None:
        try:
            from harness.services.keys import CREATOR_SERVICE_KEY

            creator = context.optional(CREATOR_SERVICE_KEY)
            if creator is not None and hasattr(creator, "skill_validator"):
                return creator.skill_validator  # type: ignore[no-any-return]
        except Exception:
            pass
    return SkillValidator
