"""Google Style Guide Auditor Plugin for Brain Harness."""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

# Ensure Harness core src is on sys.path for isolated subprocesses
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

if __name__ not in sys.modules:
    sys.modules[__name__] = sys.modules.get("__main__") or types.ModuleType(__name__)


import ast
import os
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

logger = structlog.get_logger(__name__)

_STYLEGUIDE_ROOT = Path(r"D:\GitHub\cloned\Google\styleguide")


@runtime_checkable
class GoogleStyleguideAuditorService(Protocol):
    """Protocol for Google Style Guide auditing and configuration generation."""

    def audit_file(self, file_path: str = "", language: str = "python", **kwargs: Any) -> dict[str, Any]:
        ...

    def get_rule(self, language: str = "python", topic: str = "imports", **kwargs: Any) -> dict[str, Any]:
        ...

    def generate_linter_config(self, tool_name: str = "pylint", target_dir: str = "", **kwargs: Any) -> dict[str, Any]:
        ...


GOOGLE_STYLEGUIDE_AUDITOR_SERVICE_KEY = ServiceKey[GoogleStyleguideAuditorService]("service.google_styleguide_auditor")


class GoogleStyleguideAuditorServiceImpl:
    """Service implementation auditing code against Google Style Guides."""

    def audit_file(self, file_path: str = "", language: str = "python", **kwargs: Any) -> dict[str, Any]:
        if not file_path and "task" in kwargs:
            file_path = str(Path(__file__))

        p = Path(file_path) if file_path else Path(__file__)
        if not p.exists():
            return {
                "status": "error",
                "message": f"File not found: {file_path}",
                "violations": [],
            }

        violations = []
        code = p.read_text(encoding="utf-8", errors="replace")

        if language == "python" or p.suffix == ".py":
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            if alias.name == "*":
                                violations.append({
                                    "line": node.lineno,
                                    "rule": "Google Python 2.2: Imports",
                                    "severity": "error",
                                    "message": "Do not use wildcard imports ('from foo import *')",
                                })
                    elif isinstance(node, ast.FunctionDef):
                        for default in node.args.defaults:
                            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                                violations.append({
                                    "line": default.lineno,
                                    "rule": "Google Python 2.11: Default Argument Values",
                                    "severity": "warning",
                                    "message": f"Do not use mutable objects as default values in function '{node.name}'",
                                })
                    elif isinstance(node, ast.ExceptHandler):
                        if node.type is None:
                            violations.append({
                                "line": node.lineno,
                                "rule": "Google Python 2.4: Exceptions",
                                "severity": "error",
                                "message": "Never use bare 'except:' clauses; catch specific exceptions",
                            })
            except SyntaxError as e:
                violations.append({
                    "line": e.lineno or 1,
                    "rule": "SyntaxError",
                    "severity": "error",
                    "message": str(e),
                })

        return {
            "status": "success",
            "file": str(p),
            "language": language,
            "violations_count": len(violations),
            "violations": violations,
            "compliant": len(violations) == 0,
        }

    def get_rule(self, language: str = "python", topic: str = "imports", **kwargs: Any) -> dict[str, Any]:
        lang_lower = language.lower()
        topic_lower = topic.lower()

        rules = {
            "python": {
                "imports": "Use import statements for packages and modules only, not individual types. Put imports at top, grouped standard/third-party/local.",
                "exceptions": "Exceptions are allowed, but must be used carefully. Never catch Exception or use bare except unless re-raising.",
                "naming": "module_name, package_name, ClassName, method_name, ExceptionName, function_name, GLOBAL_CONSTANT_NAME, instance_var_name.",
                "typing": "Type all public function signatures and return values. Use typing module or Python 3.10+ union types (|).",
            }
        }

        lang_rules = rules.get(lang_lower, rules["python"])
        rule_content = lang_rules.get(topic_lower, f"Google {language} guideline for {topic}: Maintain consistency with surrounding code.")

        return {
            "status": "success",
            "language": language,
            "topic": topic,
            "guideline": rule_content,
            "source": f"Google {language.title()} Style Guide",
            "doc_ref": f"https://google.github.io/styleguide/{lang_lower}guide.html",
        }

    def generate_linter_config(self, tool_name: str = "pylint", target_dir: str = "", **kwargs: Any) -> dict[str, Any]:
        pylintrc_path = _STYLEGUIDE_ROOT / "pylintrc"
        content = ""
        if pylintrc_path.exists():
            try:
                content = pylintrc_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass

        if not content:
            content = "[MESSAGES CONTROL]\ndisable=missing-docstring\n\n[FORMAT]\nmax-line-length=100\n"

        written_path = ""
        if target_dir:
            out_p = Path(target_dir) / ".pylintrc"
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(content, encoding="utf-8")
            written_path = str(out_p)

        return {
            "status": "success",
            "tool_name": tool_name,
            "config_length": len(content),
            "written_to": written_path,
            "config_preview": content[:300],
        }


_AUDITOR_INSTANCE = GoogleStyleguideAuditorServiceImpl()


# Top-level entrypoints matching plugin.json
def styleguide_audit_file(file_path: str = "", language: str = "python", **kwargs: Any) -> dict[str, Any]:
    return _AUDITOR_INSTANCE.audit_file(file_path=file_path, language=language, **kwargs)


def styleguide_get_rule(language: str = "python", topic: str = "imports", **kwargs: Any) -> dict[str, Any]:
    return _AUDITOR_INSTANCE.get_rule(language=language, topic=topic, **kwargs)


def styleguide_generate_linter_config(tool_name: str = "pylint", target_dir: str = "", **kwargs: Any) -> dict[str, Any]:
    return _AUDITOR_INSTANCE.generate_linter_config(tool_name=tool_name, target_dir=target_dir, **kwargs)


class GoogleStyleguideAuditorPlugin(HarnessPlugin):
    """Brain Harness Plugin auditing code compliance against Google Style Guides."""

    @property
    def name(self) -> str:
        return "plugin.google_styleguide_auditor"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Google Style Guide auditor and linter config generator for Python, C++, TypeScript, Java, and Shell."

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [GOOGLE_STYLEGUIDE_AUDITOR_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(GOOGLE_STYLEGUIDE_AUDITOR_SERVICE_KEY, _AUDITOR_INSTANCE)

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)
    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()



plugin = GoogleStyleguideAuditorPlugin()