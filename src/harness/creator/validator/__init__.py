"""Plugin validator — pre-flight schema, syntax, AST, signature, and sandbox verification.

Provides composable, rule-based diagnostic validation with auto-remediation:
    1. DirectoryExistenceRule
    2. ManifestSchemaRule
    3. EntrypointFileRule
    4. AstFunctionInspectionRule
    5. AstSignatureMatchingRule
    6. DependencyManifestRule
    7. JavaScriptStaticAnalysisRule
    8. SandboxDryRunRule
    9. ValidationFixer (Automated remediation engine)
"""

from __future__ import annotations

from harness.creator.validator.base import ValidationRule, _run_coro_sync
from harness.creator.validator.engine import (
    PluginValidator,
    ValidationFixer,
    ValidationPipeline,
    resolve_plugin_validator,
)
from harness.creator.validator.models import (
    RuleSeverity,
    ValidationCheck,
    ValidationContext,
    ValidationReport,
)
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

__all__ = [
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
    "resolve_plugin_validator",
]
