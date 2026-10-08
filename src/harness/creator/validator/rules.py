"""Structural, AST static analysis, and dependency validation rules."""

from __future__ import annotations

import ast
import json
import re

from harness.creator.validator.base import ValidationRule
from harness.creator.validator.models import RuleSeverity, ValidationContext
from harness.plugins.manifest import EntrypointSpec, PluginManifest


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
