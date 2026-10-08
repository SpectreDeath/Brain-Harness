"""Characterization test contract for Creator Validator decomposed package architecture.

Verifies:
1. Submodule independence and public facade parity.
2. Slotted dataclass architecture for ValidationCheck, ValidationReport, ValidationContext (Rule 12).
3. Diagnostic interface invariant: report.valid evaluation and granular checks (Rule 34).
4. Coroutine and synchronous dual-mode invocation contract (Rule 38).
5. Single-seam resolver seam (Rule 58).
6. Auto-remediation engine and rule isolation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


@pytest.mark.unit
class TestCreatorValidatorDecompositionParity:
    """Verifies submodule isolation, public export parity, and slotted contracts."""

    def test_submodule_import_isolation(self) -> None:
        """Verify each submodule can be imported independently without circular dependencies."""
        from harness.creator.validator import base, engine, models, rules, sandbox

        assert hasattr(models, "ValidationReport")
        assert hasattr(models, "ValidationCheck")
        assert hasattr(models, "RuleSeverity")
        assert hasattr(models, "ValidationContext")

        assert hasattr(base, "ValidationRule")
        assert hasattr(base, "_run_coro_sync")

        assert hasattr(rules, "DirectoryExistenceRule")
        assert hasattr(rules, "ManifestSchemaRule")
        assert hasattr(rules, "EntrypointFileRule")
        assert hasattr(rules, "AstFunctionInspectionRule")
        assert hasattr(rules, "AstSignatureMatchingRule")
        assert hasattr(rules, "DependencyManifestRule")
        assert hasattr(rules, "JavaScriptStaticAnalysisRule")

        assert hasattr(sandbox, "SandboxDryRunRule")

        assert hasattr(engine, "ValidationPipeline")
        assert hasattr(engine, "ValidationFixer")
        assert hasattr(engine, "PluginValidator")
        assert hasattr(engine, "resolve_plugin_validator")

    def test_facade_all_symbol_export_parity(self) -> None:
        """Verify the facade in __init__.py exports all 17 original symbols."""
        import harness.creator.validator as val_pkg

        expected_symbols = [
            "AstFunctionInspectionRule",
            "AstSignatureMatchingRule",
            "DependencyManifestRule",
            "DirectoryExistenceRule",
            "EntrypointFileRule",
            "JavaScriptStaticAnalysisRule",
            "ManifestSchemaRule",
            "PluginValidator",
            "RuleSeverity",
            "SandboxDryRunRule",
            "ValidationCheck",
            "ValidationContext",
            "ValidationFixer",
            "ValidationPipeline",
            "ValidationReport",
            "ValidationRule",
            "_run_coro_sync",
        ]
        for sym in expected_symbols:
            assert hasattr(val_pkg, sym), f"Facade missing original symbol: {sym}"
            assert sym in val_pkg.__all__, f"__all__ missing symbol: {sym}"

    def test_slotted_dataclass_architecture(self) -> None:
        """Verify slotted dataclasses minimize memory footprint (Rule 12)."""
        from harness.creator.validator.models import (
            RuleSeverity,
            ValidationCheck,
            ValidationContext,
            ValidationReport,
        )

        assert hasattr(ValidationCheck, "__slots__")
        assert hasattr(ValidationReport, "__slots__")
        assert hasattr(ValidationContext, "__slots__")

        check = ValidationCheck(
            name="test_check",
            passed=True,
            message="Check passed",
            severity=RuleSeverity.INFO,
        )
        assert check.name == "test_check"

        report = ValidationReport(plugin_path="/dummy/path", valid=True)
        assert report.valid is True
        assert report.plugin_path == "/dummy/path"

        ctx = ValidationContext(path=Path("/dummy/path"))
        assert ctx.report.valid is True

    def test_diagnostic_report_interface_invariant_rule_34(self) -> None:
        """Verify Rule 34: ValidationReport has .valid, NOT .passed, and provides checks."""
        from harness.creator.validator.models import (
            RuleSeverity,
            ValidationCheck,
            ValidationReport,
        )

        report = ValidationReport(plugin_path="/dummy/path", valid=True)
        # Invariant: report has .valid boolean
        assert hasattr(report, "valid")
        assert isinstance(report.valid, bool)

        # Invariant: report does NOT have .passed
        assert not hasattr(report, "passed")

        # Invariant: granular checks inspection
        check = ValidationCheck(
            name="RuleCheck",
            passed=True,
            message="Check succeeded",
            severity=RuleSeverity.INFO,
            category="structural",
        )
        report.checks.append(check)
        assert len(report.checks) == 1
        assert report.checks[0].name == "RuleCheck"
        assert report.checks[0].passed is True

        # Test dictionary conversion and cli formatting
        data = report.to_dict()
        assert data["valid"] is True
        assert len(data["checks"]) == 1
        assert data["checks"][0]["name"] == "RuleCheck"

        cli_summary = report.format_cli()
        assert "PASS" in cli_summary
        assert "RuleCheck" in cli_summary


@pytest.mark.unit
class TestCreatorValidatorEngineAndRules:
    """Verifies rule behavior, dual-mode execution (Rule 38), and single-seam resolver (Rule 58)."""

    @pytest.mark.asyncio
    async def test_coroutine_validation_invocation(self, tmp_path: Path) -> None:
        """Verify asynchronous invocation (Rule 38)."""
        from harness.creator.validator.engine import PluginValidator

        target = tmp_path / "test_async_plugin"
        target.mkdir()
        manifest_data = {
            "name": "async-plugin",
            "version": "0.1.0",
            "language": "python",
            "entrypoint": "main.py",
            "entrypoints": [{"name": "run", "parameters": []}],
        }
        (target / "plugin.json").write_text(json.dumps(manifest_data), encoding="utf-8")
        (target / "main.py").write_text("def run():\n    return {'status': 'ok'}\n", encoding="utf-8")

        report = await PluginValidator.validate(target, dry_run=False)
        assert report.valid is True
        assert any(c.name == "Manifest Schema" and c.passed for c in report.checks)
        assert any(c.name == "AST Function Inspection" and c.passed for c in report.checks)

    def test_synchronous_validation_invocation(self, tmp_path: Path) -> None:
        """Verify synchronous invocation via validate_sync (Rule 38)."""
        from harness.creator.validator.engine import PluginValidator

        target = tmp_path / "test_sync_plugin"
        target.mkdir()
        manifest_data = {
            "name": "sync-plugin",
            "version": "0.1.0",
            "language": "python",
            "entrypoint": "main.py",
            "entrypoints": [{"name": "process", "parameters": []}],
        }
        (target / "plugin.json").write_text(json.dumps(manifest_data), encoding="utf-8")
        (target / "main.py").write_text("def process():\n    return {'status': 'ok'}\n", encoding="utf-8")

        report = PluginValidator.validate_sync(target, dry_run=False)
        assert report.valid is True
        assert any(c.name == "Manifest Schema" and c.passed for c in report.checks)
        assert any(c.name == "AST Function Inspection" and c.passed for c in report.checks)

    def test_single_seam_resolver(self) -> None:
        """Verify single-seam resolver function (Rule 58)."""
        from harness.creator.validator.engine import (
            PluginValidator,
            resolve_plugin_validator,
        )

        # Default resolution without context returns PluginValidator
        validator = resolve_plugin_validator(None)
        assert validator is PluginValidator or isinstance(validator, PluginValidator)

    @pytest.mark.asyncio
    async def test_auto_remediation_pipeline(self, tmp_path: Path) -> None:
        """Verify auto-remediation synthesizes missing entrypoints and stubs."""
        from harness.creator.validator.engine import ValidationFixer

        plugin_dir = tmp_path / "broken_plugin"
        plugin_dir.mkdir()
        manifest_data = {
            "name": "broken-plugin",
            "version": "0.1.0",
            "language": "python",
            "entrypoint": "main.py",
            "entrypoints": [{"name": "auto_heal", "parameters": []}],
        }
        (plugin_dir / "plugin.json").write_text(json.dumps(manifest_data), encoding="utf-8")
        # Missing main.py entirely

        report = await ValidationFixer.remediate(plugin_dir)
        assert (plugin_dir / "main.py").exists()
        assert len(report.remediations) > 0

    def test_sync_auto_remediation(self, tmp_path: Path) -> None:
        """Verify synchronous auto-remediation via remediate_sync."""
        from harness.creator.validator.engine import ValidationFixer

        plugin_dir = tmp_path / "broken_sync_plugin"
        plugin_dir.mkdir()
        # No manifest, no entrypoint
        report = ValidationFixer.remediate_sync(plugin_dir)
        assert (plugin_dir / "plugin.json").exists()
        assert len(report.remediations) > 0
