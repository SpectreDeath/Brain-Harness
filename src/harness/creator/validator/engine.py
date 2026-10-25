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


class DualModeValidationReport(ValidationReport):
    """Awaitable and synchronous proxy wrapper for ValidationReport.

    Eliminates the async/sync footgun (Track 0 P2):
    Can be awaited (`await PluginValidator.validate(...)`) in asynchronous
    contexts, or accessed directly (`report.valid`, `report.checks`) in synchronous
    contexts without raising unawaited coroutine errors.
    """

    __slots__ = ("_coro_fn", "_report")

    def __init__(self, coro_fn: Any) -> None:
        object.__setattr__(self, "_coro_fn", coro_fn)
        object.__setattr__(self, "_report", None)

    def _resolve(self) -> ValidationReport:
        report = object.__getattribute__(self, "_report")
        if report is None:
            coro_fn = object.__getattribute__(self, "_coro_fn")
            report = cast(ValidationReport, _run_coro_sync(coro_fn()))
            object.__setattr__(self, "_report", report)
        return report

    def __await__(self) -> Any:
        async def _await_inner() -> ValidationReport:
            report = object.__getattribute__(self, "_report")
            if report is None:
                coro_fn = object.__getattribute__(self, "_coro_fn")
                report = await coro_fn()
                object.__setattr__(self, "_report", report)
            return report

        return _await_inner().__await__()

    @property
    def plugin_path(self) -> str:
        return self._resolve().plugin_path

    @property
    def valid(self) -> bool:
        return self._resolve().valid

    @property
    def checks(self) -> list[Any]:
        return self._resolve().checks

    @property
    def errors(self) -> list[str]:
        return self._resolve().errors

    @property
    def warnings(self) -> list[str]:
        return self._resolve().warnings

    @property
    def remediations(self) -> list[str]:
        return self._resolve().remediations

    @property
    def manifest(self) -> Any:
        return self._resolve().manifest

    def to_dict(self) -> dict[str, Any]:
        return self._resolve().to_dict()

    def format_cli(self) -> str:
        return self._resolve().format_cli()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._resolve(), name)


class ValidationFixer:
    """Authoritative auto-remediation engine for fixing plugin structure issues."""

    @classmethod
    def remediate(cls, plugin_dir: Path | str) -> DualModeValidationReport:
        """Run validation pipeline in remediation mode to auto-repair issues."""
        async def _exec() -> ValidationReport:
            pipeline = ValidationPipeline()
            return await pipeline.execute(plugin_dir, remediate=True)

        return DualModeValidationReport(_exec)

    @classmethod
    def remediate_sync(cls, plugin_dir: Path | str) -> ValidationReport:
        """Synchronously auto-repair plugin issues."""
        return cls.remediate(plugin_dir)._resolve()


class PluginValidator:
    """Authoritative validation facade for plugin directories.

    Follows Rule 38 & Track 0 P2: provides dual-mode invocation where `validate()`
    can be awaited asynchronously (`await PluginValidator.validate(...)`) or accessed
    directly synchronously (`report = PluginValidator.validate(...)`), as well as
    the explicit synchronous `validate_sync()` invocation entrypoint.
    """

    @classmethod
    def validate(
        cls,
        plugin_dir: Path | str,
        *,
        dry_run: bool = False,
        timeout: float = 15.0,
        remediate: bool = False,
        pipeline: ValidationPipeline | None = None,
    ) -> DualModeValidationReport:
        """Run all pre-flight and runtime diagnostic checks on a plugin directory."""
        async def _exec() -> ValidationReport:
            active_pipeline = pipeline or ValidationPipeline()
            return await active_pipeline.execute(
                plugin_dir,
                dry_run=dry_run,
                timeout=timeout,
                remediate=remediate,
            )

        return DualModeValidationReport(_exec)

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
        return cls.validate(
            plugin_dir,
            dry_run=dry_run,
            timeout=timeout,
            remediate=remediate,
            pipeline=pipeline,
        )._resolve()

    @classmethod
    def remediate(cls, plugin_dir: Path | str) -> DualModeValidationReport:
        """Run validation pipeline in remediation mode."""
        return cls.validate(plugin_dir, remediate=True)


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
