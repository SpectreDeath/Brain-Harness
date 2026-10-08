"""Diagnostic data structures and execution context for plugin validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from harness.plugins.manifest import PluginManifest


class RuleSeverity(str, Enum):
    """Severity classification for validation checks."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(slots=True)
class ValidationCheck:
    """Represents the outcome of a single diagnostic check."""

    name: str
    passed: bool
    message: str
    severity: RuleSeverity = RuleSeverity.INFO
    category: str = "general"
    details: dict[str, Any] = field(default_factory=dict)
    remediated: bool = False


@dataclass(slots=True)
class ValidationReport:
    """Comprehensive diagnostic report for a plugin package.

    Follows Rule 34: Exposes .valid boolean status (never .passed) and granular checks.
    """

    plugin_path: str
    valid: bool
    checks: list[ValidationCheck] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    remediations: list[str] = field(default_factory=list)
    manifest: PluginManifest | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert report to serializable dict."""
        return {
            "plugin_path": self.plugin_path,
            "valid": self.valid,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "message": c.message,
                    "severity": c.severity.value,
                    "category": c.category,
                    "details": c.details,
                    "remediated": c.remediated,
                }
                for c in self.checks
            ],
            "errors": self.errors,
            "warnings": self.warnings,
            "remediations": self.remediations,
            "manifest": self.manifest.model_dump() if self.manifest else None,
        }

    def format_cli(self) -> str:
        """Format the report into a colorized ASCII terminal summary."""
        status_sym = "✓ PASS" if self.valid else "✗ FAIL"
        lines = [
            f"Plugin Pre-Flight Validation Report: {self.plugin_path}",
            "━" * 58,
            f"Overall Status: {status_sym}",
            "",
            "Diagnostic Checks:",
        ]
        for c in self.checks:
            if not c.passed:
                mark = "  ✗"
                sev_badge = f"[{c.severity.value.upper()}]"
            elif c.severity == RuleSeverity.WARNING:
                mark = "  ⚠"
                sev_badge = "[WARNING]"
            else:
                mark = "  ✓"
                sev_badge = ""
            lines.append(f"{mark} {c.name:<30} {sev_badge} {c.message}")

        if self.remediations:
            lines.append("\nApplied Auto-Remediations:")
            for fix in self.remediations:
                lines.append(f"  🔧 {fix}")

        if self.errors:
            lines.append("\nErrors:")
            for err in self.errors:
                lines.append(f"  • {err}")

        if self.warnings:
            lines.append("\nWarnings:")
            for warn in self.warnings:
                lines.append(f"  • {warn}")

        return "\n".join(lines)


@dataclass(slots=True)
class ValidationContext:
    """Shared execution context passed through the validation pipeline."""

    path: Path
    dry_run: bool = False
    timeout: float = 15.0
    remediate: bool = False
    report: ValidationReport = field(init=False)
    manifest: PluginManifest | None = None

    def __post_init__(self) -> None:
        self.report = ValidationReport(plugin_path=str(self.path), valid=True)

    def add_pass(
        self,
        name: str,
        message: str,
        details: dict[str, Any] | None = None,
        category: str = "general",
    ) -> None:
        self.report.checks.append(
            ValidationCheck(
                name=name,
                passed=True,
                message=message,
                severity=RuleSeverity.INFO,
                category=category,
                details=details or {},
            )
        )

    def add_fail(
        self,
        name: str,
        error: str,
        severity: RuleSeverity = RuleSeverity.ERROR,
        details: dict[str, Any] | None = None,
        category: str = "general",
    ) -> None:
        self.report.valid = False
        self.report.errors.append(error)
        self.report.checks.append(
            ValidationCheck(
                name=name,
                passed=False,
                message=error,
                severity=severity,
                category=category,
                details=details or {},
            )
        )

    def add_warn(
        self,
        name: str,
        warning: str,
        details: dict[str, Any] | None = None,
        category: str = "general",
    ) -> None:
        self.report.warnings.append(warning)
        self.report.checks.append(
            ValidationCheck(
                name=name,
                passed=True,
                message=f"Warning: {warning}",
                severity=RuleSeverity.WARNING,
                category=category,
                details=details or {},
            )
        )

    def add_remediation(self, fix_description: str) -> None:
        self.report.remediations.append(fix_description)
