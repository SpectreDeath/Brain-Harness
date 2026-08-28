"""Plugin validator — pre-flight schema, syntax, AST, signature, and sandbox verification.

Provides composable, rule-based diagnostic validation with auto-remediation:
    1. DirectoryExistenceRule
    2. ManifestSchemaRule
    3. EntrypointFileRule
    4. AstFunctionInspectionRule
    5. AstSignatureMatchingRule
    6. SandboxDryRunRule
    7. ValidationFixer (Automated remediation engine)
"""

from __future__ import annotations

import ast
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, cast

import structlog

from harness.plugins.manifest import EntrypointSpec, PluginManifest
from harness.plugins.sandbox import SandboxExecutorFactory

logger = structlog.get_logger()


class RuleSeverity(str, Enum):
    """Severity classification for validation checks."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationCheck:
    """Represents the outcome of a single diagnostic check."""

    name: str
    passed: bool
    message: str
    severity: RuleSeverity = RuleSeverity.INFO
    category: str = "general"
    details: dict[str, Any] = field(default_factory=dict)
    remediated: bool = False


@dataclass
class ValidationReport:
    """Comprehensive diagnostic report for a plugin package."""

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


@dataclass
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


class ValidationRule(ABC):
    """Abstract validation check rule."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the validation check rule."""

    @property
    def category(self) -> str:
        """Category domain of the rule."""
        return "structural"

    @abstractmethod
    async def validate(self, ctx: ValidationContext) -> bool:
        """Execute validation rule. Returns True if pipeline can continue, False if fatal."""


class DirectoryExistenceRule(ValidationRule):
    """Verifies that the target plugin path exists and is a directory."""

    @property
    def name(self) -> str:
        return "Directory Existence"

    async def validate(self, ctx: ValidationContext) -> bool:
        if not ctx.path.exists() or not ctx.path.is_dir():
            ctx.add_fail(
                self.name,
                f"Directory does not exist: {ctx.path}",
                severity=RuleSeverity.CRITICAL,
                category=self.category,
            )
            return False
        ctx.add_pass(self.name, f"Found directory at {ctx.path}", category=self.category)
        return True


class ManifestSchemaRule(ValidationRule):
    """Verifies that plugin.json exists, parses cleanly, and validates against PluginManifest schema."""

    @property
    def name(self) -> str:
        return "Manifest Schema"

    async def validate(self, ctx: ValidationContext) -> bool:
        manifest_file = ctx.path / "plugin.json"
        if not manifest_file.exists():
            if ctx.remediate:
                # Auto-remediate missing manifest
                inferred_name = ctx.path.name
                manifest = PluginManifest(
                    name=inferred_name,
                    version="0.1.0",
                    description=f"Auto-generated manifest for {inferred_name}",
                    language="python",
                    entrypoint="main.py",
                    provides=[f"tool.{inferred_name}"],
                    entrypoints=[EntrypointSpec(name="execute", description="Default handler")],
                )
                manifest.to_file(manifest_file)
                ctx.manifest = manifest
                ctx.report.manifest = manifest
                ctx.add_remediation(f"Created default plugin.json manifest for '{inferred_name}'")
                ctx.add_pass(self.name, f"Synthesized default schema for '{inferred_name}'", category=self.category)
                return True

            ctx.add_fail(self.name, "Missing plugin.json manifest file", severity=RuleSeverity.CRITICAL, category=self.category)
            return False

        try:
            manifest_text = manifest_file.read_text(encoding="utf-8")
            manifest_json = json.loads(manifest_text)
            manifest = PluginManifest.model_validate(manifest_json)
            ctx.manifest = manifest
            ctx.report.manifest = manifest
            ctx.add_pass(
                self.name,
                f"Valid schema for '{manifest.name}' v{manifest.version}",
                details={"name": manifest.name, "version": manifest.version, "language": manifest.language},
                category=self.category,
            )
            return True
        except Exception as e:
            ctx.add_fail(self.name, f"Failed to parse plugin.json: {e}", severity=RuleSeverity.ERROR, category=self.category)
            return False


class EntrypointFileRule(ValidationRule):
    """Verifies that the entrypoint source script exists on disk."""

    @property
    def name(self) -> str:
        return "Entrypoint File"

    async def validate(self, ctx: ValidationContext) -> bool:
        if ctx.manifest is None:
            return False

        entrypoint_name = ctx.manifest.entrypoint or ("main.py" if ctx.manifest.language == "python" else "index.js")
        entrypoint_path = ctx.path / entrypoint_name
        if not entrypoint_path.exists():
            if ctx.remediate and ctx.manifest.language == "python":
                # Create basic entrypoint stub
                entrypoint_path.write_text(
                    '"""Main entrypoint stub."""\n\nfrom typing import Any\n\n\ndef execute(task: str = "", **kwargs: Any) -> dict[str, Any]:\n    return {"status": "ok", "task": task}\n',
                    encoding="utf-8",
                )
                ctx.add_remediation(f"Created boilerplate entrypoint '{entrypoint_name}'")
                ctx.add_pass(self.name, f"Created missing entrypoint '{entrypoint_name}'", category=self.category)
                return True

            ctx.add_fail(self.name, f"Entrypoint file '{entrypoint_name}' not found in {ctx.path}", severity=RuleSeverity.ERROR, category=self.category)
            return False

        ctx.add_pass(self.name, f"Found entrypoint '{entrypoint_name}'", category=self.category)
        return True


class AstFunctionInspectionRule(ValidationRule):
    """Statically parses Python entrypoints using AST to verify all declared entrypoint functions exist."""

    @property
    def name(self) -> str:
        return "AST Function Inspection"

    @property
    def category(self) -> str:
        return "static_analysis"

    async def validate(self, ctx: ValidationContext) -> bool:
        if ctx.manifest is None or ctx.manifest.language != "python":
            return True

        entrypoint_name = ctx.manifest.entrypoint or "main.py"
        entrypoint_path = ctx.path / entrypoint_name
        if not entrypoint_path.exists():
            return False

        try:
            code_content = entrypoint_path.read_text(encoding="utf-8")
            tree = ast.parse(code_content, filename=str(entrypoint_path))
            defined_functions = {
                node.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            }

            missing_funcs = [
                ep.name for ep in ctx.manifest.entrypoints if ep.name not in defined_functions
            ]

            if missing_funcs:
                if ctx.remediate:
                    # Auto-append missing function stubs to entrypoint file
                    has_typing_import = bool(
                        re.search(r"^\s*(from\s+typing\s+import|import\s+typing)\b", code_content, re.MULTILINE)
                    )
                    stubs = [
                        f'\ndef {fn}(task: str = "", **kwargs: Any) -> dict[str, Any]:\n    """Auto-remediated stub for {fn}."""\n    return {{"status": "ok", "action": "{fn}", "result": task}}\n'
                        for fn in missing_funcs
                    ]
                    code_to_write = code_content
                    if not has_typing_import:
                        if (
                            tree.body
                            and isinstance(tree.body[0], ast.Expr)
                            and isinstance(tree.body[0].value, ast.Constant)
                            and isinstance(tree.body[0].value.value, str)
                            and hasattr(tree.body[0], "end_lineno")
                            and tree.body[0].end_lineno is not None
                        ):
                            doc_end = tree.body[0].end_lineno
                            lines = code_content.splitlines(keepends=True)
                            head = "".join(lines[:doc_end])
                            tail = "".join(lines[doc_end:])
                            code_to_write = head + "\n\nfrom typing import Any\n" + tail
                        else:
                            code_to_write = "from typing import Any\n\n" + code_content

                    new_code = code_to_write.rstrip() + "\n" + "\n".join(stubs)
                    entrypoint_path.write_text(new_code, encoding="utf-8")
                    ctx.add_remediation(f"Appended function stubs in {entrypoint_name} for: {missing_funcs}")
                    ctx.add_pass(self.name, f"Remediated missing functions: {missing_funcs}", category=self.category)
                    return True

                ctx.add_fail(
                    self.name,
                    f"Entrypoint functions declared in manifest but missing in {entrypoint_name}: {missing_funcs}",
                    severity=RuleSeverity.ERROR,
                    details={"declared": [e.name for e in ctx.manifest.entrypoints], "missing": missing_funcs},
                    category=self.category,
                )
                return False

            ctx.add_pass(
                self.name,
                f"All {len(ctx.manifest.entrypoints)} declared entrypoints exist in source code",
                details={"functions": list(defined_functions)},
                category=self.category,
            )
            return True
        except SyntaxError as se:
            ctx.add_fail(self.name, f"Syntax error in {entrypoint_name}: {se}", severity=RuleSeverity.ERROR, category=self.category)
            return False


class AstSignatureMatchingRule(ValidationRule):
    """Statically verifies that declared manifest parameter types align with Python entrypoint signatures."""

    @property
    def name(self) -> str:
        return "AST Signature Matching"

    @property
    def category(self) -> str:
        return "static_analysis"

    async def validate(self, ctx: ValidationContext) -> bool:
        if ctx.manifest is None or ctx.manifest.language != "python":
            return True

        entrypoint_name = ctx.manifest.entrypoint or "main.py"
        entrypoint_path = ctx.path / entrypoint_name
        if not entrypoint_path.exists():
            return False

        try:
            code_content = entrypoint_path.read_text(encoding="utf-8")
            tree = ast.parse(code_content, filename=str(entrypoint_path))

            fn_args: dict[str, list[str]] = {}
            fn_has_kwarg: dict[str, bool] = {}
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    posonly = [a.arg for a in getattr(node.args, "posonlyargs", [])]
                    standard = [a.arg for a in node.args.args]
                    kwonly = [a.arg for a in getattr(node.args, "kwonlyargs", [])]
                    fn_args[node.name] = posonly + standard + kwonly
                    fn_has_kwarg[node.name] = node.args.kwarg is not None

            warnings: list[str] = []
            for ep in ctx.manifest.entrypoints:
                if ep.name in fn_args:
                    declared_params = [p.name for p in ep.parameters if p.required]
                    actual_args = fn_args[ep.name]
                    has_kwarg = fn_has_kwarg.get(ep.name, False)

                    # If function accepts **kwargs, any undeclared or additional parameter is accepted
                    if not has_kwarg:
                        for p_name in declared_params:
                            if p_name not in actual_args:
                                warnings.append(f"Function '{ep.name}' signature may lack parameter '{p_name}'")

            if warnings:
                for w in warnings:
                    ctx.add_warn(self.name, w, category=self.category)
            else:
                ctx.add_pass(self.name, "Entrypoint parameter signatures match manifest specifications", category=self.category)

            return True
        except Exception as e:
            ctx.add_warn(self.name, f"Signature inspection skipped: {e}", category=self.category)
            return True


class DependencyManifestRule(ValidationRule):
    """Verifies that package dependency files (requirements.txt or package.json) are present and consistent."""

    @property
    def name(self) -> str:
        return "Dependency Manifest"

    @property
    def category(self) -> str:
        return "dependencies"

    async def validate(self, ctx: ValidationContext) -> bool:
        if ctx.manifest is None:
            return True

        lang = (ctx.manifest.language or "python").lower()

        if lang == "python":
            req_file = ctx.path / "requirements.txt"
            declared_deps = ctx.manifest.dependencies or []

            if not req_file.exists():
                if declared_deps:
                    if ctx.remediate:
                        req_file.write_text("\n".join(declared_deps) + "\n", encoding="utf-8")
                        ctx.add_remediation(f"Created requirements.txt with {len(declared_deps)} dependencies")
                        ctx.add_pass(self.name, f"Synthesized requirements.txt with {declared_deps}", category=self.category)
                        return True
                    ctx.add_warn(self.name, f"Missing requirements.txt for declared dependencies: {declared_deps}", category=self.category)
                return True

            try:
                content = req_file.read_text(encoding="utf-8")
                req_lines = [line.strip().lower() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]

                missing_in_file = []
                for dep in declared_deps:
                    dep_pkg = dep.split("=")[0].split(">")[0].split("<")[0].strip().lower()
                    if not any(dep_pkg in line for line in req_lines):
                        missing_in_file.append(dep)

                if missing_in_file:
                    if ctx.remediate:
                        new_content = content.rstrip() + "\n" + "\n".join(missing_in_file) + "\n"
                        req_file.write_text(new_content, encoding="utf-8")
                        ctx.add_remediation(f"Appended missing dependencies to requirements.txt: {missing_in_file}")
                        ctx.add_pass(self.name, f"Synchronized requirements.txt with: {missing_in_file}", category=self.category)
                    else:
                        ctx.add_warn(self.name, f"Declared dependencies missing from requirements.txt: {missing_in_file}", category=self.category)
                else:
                    ctx.add_pass(self.name, "requirements.txt matches manifest dependencies", category=self.category)
            except Exception as e:
                ctx.add_warn(self.name, f"Failed to inspect requirements.txt: {e}", category=self.category)

            return True

        elif lang in ("javascript", "typescript"):
            pkg_file = ctx.path / "package.json"
            if not pkg_file.exists():
                if ctx.remediate:
                    pkg_data = {
                        "name": ctx.manifest.name,
                        "version": ctx.manifest.version,
                        "description": ctx.manifest.description,
                        "main": ctx.manifest.entrypoint or "index.js",
                        "type": "module",
                        "dependencies": {dep: "*" for dep in (ctx.manifest.dependencies or [])},
                    }
                    pkg_file.write_text(json.dumps(pkg_data, indent=2), encoding="utf-8")
                    ctx.add_remediation(f"Created package.json for '{ctx.manifest.name}'")
                    ctx.add_pass(self.name, "Synthesized default package.json", category=self.category)
                    return True
                if ctx.manifest.dependencies:
                    ctx.add_warn(self.name, "Missing package.json for JavaScript/TypeScript plugin", category=self.category)
            else:
                try:
                    pkg_json = json.loads(pkg_file.read_text(encoding="utf-8"))
                    ctx.add_pass(self.name, f"Valid package.json ({pkg_json.get('name', ctx.manifest.name)})", category=self.category)
                except Exception as e:
                    ctx.add_fail(self.name, f"Malformed package.json: {e}", severity=RuleSeverity.ERROR, category=self.category)
                    return False

        return True


class JavaScriptStaticAnalysisRule(ValidationRule):
    """Statically verifies JavaScript / TypeScript entrypoints export declared entrypoint functions."""

    @property
    def name(self) -> str:
        return "JavaScript Static Analysis"

    @property
    def category(self) -> str:
        return "static_analysis"

    async def validate(self, ctx: ValidationContext) -> bool:
        if ctx.manifest is None or (ctx.manifest.language or "").lower() not in ("javascript", "typescript"):
            return True

        entrypoint_name = ctx.manifest.entrypoint or ("index.ts" if ctx.manifest.language == "typescript" else "index.js")
        entrypoint_path = ctx.path / entrypoint_name
        if not entrypoint_path.exists():
            return False

        try:
            content = entrypoint_path.read_text(encoding="utf-8")
            missing_funcs: list[str] = []

            for ep in ctx.manifest.entrypoints:
                fn_name = ep.name
                # Look for common JS/TS export or function declarations
                patterns = [
                    rf"\bexport\s+(?:async\s+)?function\s+{re.escape(fn_name)}\b",
                    rf"\bexport\s+const\s+{re.escape(fn_name)}\b",
                    rf"\bfunction\s+{re.escape(fn_name)}\b",
                    rf"\bexports\.{re.escape(fn_name)}\b",
                    rf"\bmodule\.exports\b.*{re.escape(fn_name)}",
                ]
                if not any(re.search(pat, content) for pat in patterns):
                    missing_funcs.append(fn_name)

            if missing_funcs:
                if ctx.remediate:
                    stubs = [
                        f"\nexport async function {fn}(task = '', kwargs = {{}}) {{\n"
                        f"  return {{ status: 'ok', action: '{fn}', result: task, extra: kwargs }};\n"
                        f"}}\n"
                        for fn in missing_funcs
                    ]
                    entrypoint_path.write_text(content + "\n" + "\n".join(stubs), encoding="utf-8")
                    ctx.add_remediation(f"Appended JS/TS export stubs for: {missing_funcs}")
                    ctx.add_pass(self.name, f"Remediated missing JS/TS exports: {missing_funcs}", category=self.category)
                    return True

                ctx.add_fail(
                    self.name,
                    f"Entrypoints declared in manifest but missing in {entrypoint_name}: {missing_funcs}",
                    severity=RuleSeverity.ERROR,
                    details={"missing": missing_funcs},
                    category=self.category,
                )
                return False

            ctx.add_pass(
                self.name,
                f"All {len(ctx.manifest.entrypoints)} declared JS/TS entrypoints found in {entrypoint_name}",
                category=self.category,
            )
            return True
        except Exception as e:
            ctx.add_warn(self.name, f"JS/TS static analysis skipped: {e}", category=self.category)
            return True


class SandboxDryRunRule(ValidationRule):
    """Optionally boots the sandbox executor and tests tool invocation over JSON-RPC."""

    @property
    def name(self) -> str:
        return "Sandbox Dry-Run"

    @property
    def category(self) -> str:
        return "runtime"

    async def validate(self, ctx: ValidationContext) -> bool:
        if not ctx.dry_run or not ctx.report.valid or not ctx.manifest or not ctx.manifest.entrypoints:
            return True

        try:
            executor = SandboxExecutorFactory.create(ctx.manifest, ctx.path)
            if executor is None:
                ctx.add_warn(self.name, "Skipped (no executor available for dry-run)", category=self.category)
                return True

            await executor.start()
            try:
                first_ep = ctx.manifest.entrypoints[0]
                res = await executor.execute(first_ep.name, {"task": "validator-dry-run"}, timeout=ctx.timeout)
                if res.get("status") == "error":
                    ctx.add_fail(
                        self.name,
                        f"Sandbox execution failed for '{first_ep.name}': {res.get('error')}",
                        severity=RuleSeverity.ERROR,
                        details=res,
                        category=self.category,
                    )
                    return False
                ctx.add_pass(
                    self.name,
                    f"Successfully executed '{first_ep.name}' in sandbox",
                    details=res,
                    category=self.category,
                )
                return True
            finally:
                await executor.stop()
        except Exception as e:
            ctx.add_fail(self.name, f"Sandbox dry-run error: {e}", severity=RuleSeverity.ERROR, category=self.category)
            return False


def _run_coro_sync(coro: Any) -> Any:
    """Safely run a coroutine synchronously even within existing event loops."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


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


class PluginValidator:
    """Authoritative validation facade for plugin directories."""

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
]
