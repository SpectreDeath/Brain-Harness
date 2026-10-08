"""Execution pipeline, auto-remediator, and authoritative validator facade."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from harness.creator.validator.base import ValidationRule, _run_coro_sync
from harness.creator.validator.models import ValidationContext, ValidationReport
from harness.creator.validator.rules import (
    AstFunctionInspectionRule,
    AstSignatureMatchingRule,
    DependencyManifestRule,
    DirectoryExistenceRule,
    EntrypointFileRule,
    JavaScriptStaticAnalysisRule,
    ManifestSchemaRule,
)
from harness.creator.validator.sandbox import SandboxDryRunRule


class ValidationPipeline:
    """Authoritative composite pipeline running validation rules sequentially."""

    def __init__(self, rules: list[ValidationRule] | None = None) -> None:
        self.rules = list(rules) if rules is not None else self.default_rules()

    @classmethod
    def default_rules(cls) -> list[ValidationRule]:
        return [
            DirectoryExistenceRule(),
            ManifestSchemaRule(),
            EntrypointFileRule(),
            AstFunctionInspectionRule(),
            AstSignatureMatchingRule(),
            DependencyManifestRule(),
            JavaScriptStaticAnalysisRule(),
            SandboxDryRunRule(),
        ]

    def add_rule(self, rule: ValidationRule) -> None:
        self.rules.append(rule)

    async def execute(
        self,
        plugin_dir: Path | str,
        *,
        dry_run: bool = False,
        timeout: float = 15.0,
        remediate: bool = False,
    ) -> ValidationReport:
        path = Path(plugin_dir).resolve()
        ctx = ValidationContext(path=path, dry_run=dry_run, timeout=timeout, remediate=remediate)

        for rule in self.rules:
            should_continue = await rule.validate(ctx)
            if not should_continue:
                break

        return ctx.report


class ValidationFixer:
    """Authoritative auto-remediation engine for fixing plugin structure issues."""

    @classmethod
    async def remediate(cls, plugin_dir: Path | str) -> ValidationReport:
        """Run validation pipeline in remediation mode to auto-repair issues."""
        pipeline = ValidationPipeline()
        return await pipeline.execute(plugin_dir, remediate=True)

    @classmethod
    def remediate_sync(cls, plugin_dir: Path | str) -> ValidationReport:
        """Synchronously auto-repair plugin issues."""
        return cast(ValidationReport, _run_coro_sync(cls.remediate(plugin_dir)))


class PluginValidator:
    """Authoritative validation facade for plugin directories.

    Follows Rule 38: provides both asynchronous coroutine `validate()` and
    synchronous `validate_sync()` invocation entrypoints.
    """

    @classmethod
    async def validate(
        cls,
        plugin_dir: Path | str,
        *,
        dry_run: bool = False,
        timeout: float = 15.0,
        remediate: bool = False,
        pipeline: ValidationPipeline | None = None,
    ) -> ValidationReport:
        """Run all pre-flight and runtime diagnostic checks on a plugin directory."""
        active_pipeline = pipeline or ValidationPipeline()
        return await active_pipeline.execute(
            plugin_dir,
            dry_run=dry_run,
            timeout=timeout,
            remediate=remediate,
        )

    @classmethod
    def validate_sync(
        cls,
        plugin_dir: Path | str,
        *,
        dry_run: bool = False,
        timeout: float = 15.0,
        remediate: bool = False,
        pipeline: ValidationPipeline | None = None,
    ) -> ValidationReport:
        """Synchronous helper for validating a plugin directory."""
        return cast(
            ValidationReport,
            _run_coro_sync(
                cls.validate(
                    plugin_dir,
                    dry_run=dry_run,
                    timeout=timeout,
                    remediate=remediate,
                    pipeline=pipeline,
                )
            ),
        )

    @classmethod
    async def remediate(cls, plugin_dir: Path | str) -> ValidationReport:
        """Run validation pipeline in remediation mode."""
        return await cls.validate(plugin_dir, remediate=True)


def resolve_plugin_validator(context: Any = None) -> type[PluginValidator] | PluginValidator:
    """Single-seam resolver for PluginValidator service (Rule 58).

    Resolves configured validator from IoC container if available, otherwise
    falls back to the authoritative PluginValidator class.
    """
    if context is not None:
        try:
            from harness.services.keys import CREATOR_SERVICE_KEY

            creator = context.optional(CREATOR_SERVICE_KEY)
            if creator is not None and hasattr(creator, "validator"):
                return creator.validator  # type: ignore[no-any-return]
        except Exception:
            pass
    return PluginValidator
