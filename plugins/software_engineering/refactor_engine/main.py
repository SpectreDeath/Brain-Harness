"""AST refactoring engine, unused function identifier, and function extractor plugin."""

from __future__ import annotations

import ast
from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.refactor_engine import (
    REFACTOR_ENGINE_KEY,
    FunctionExtractResult,
    RefactorEngineService,
    UnusedFunctionsResult,
)

logger = structlog.get_logger(__name__)


def find_unused_functions(code: str) -> dict[str, Any]:
    """Find declared top-level functions in a module that are never invoked within that module."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"status": "error", "error": f"Syntax error: {e!s}"}

    declared: dict[str, int] = {}
    called: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("__") and not node.name.startswith("test_"):
                declared[node.name] = node.lineno
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)

    unused: list[dict[str, Any]] = [
        {"name": name, "line": line}
        for name, line in declared.items()
        if name not in called
    ]

    return {
        "status": "ok",
        "total_functions": len(declared),
        "unused_count": len(unused),
        "unused_functions": unused,
    }


def extract_function_preview(
    code: str,
    start_line: int,
    end_line: int,
    new_func_name: str,
) -> dict[str, Any]:
    """Generate a refactored preview extracting lines into a new function."""
    lines = code.splitlines()

    if start_line < 1 or end_line > len(lines) or start_line > end_line:
        return {"status": "error", "error": "Invalid line range"}

    extracted_lines = lines[start_line - 1 : end_line]
    indent = "    "
    body_indented = "\n".join(f"{indent}{ln.strip()}" for ln in extracted_lines if ln.strip())

    func_def = f"def {new_func_name}():\n{body_indented}\n"

    # Replace extracted range with function call
    new_lines = [
        *lines[: start_line - 1],
        f"{lines[start_line - 1][:len(lines[start_line - 1]) - len(lines[start_line - 1].lstrip())]}{new_func_name}()",
        *lines[end_line:],
    ]

    refactored_code = f"{func_def}\n" + "\n".join(new_lines)

    return {
        "status": "ok",
        "new_function_name": new_func_name,
        "extracted_lines_count": len(extracted_lines),
        "function_definition": func_def,
        "refactored_preview": refactored_code,
    }


class RefactorEnginePlugin(HarnessPlugin, RefactorEngineService):
    """Harness Plugin providing AST-based unused function detection and function extraction."""

    name = "plugin.refactor_engine"
    version = "1.0.0"
    description = "Python AST refactoring engine, dead/unused code identifier, and function extraction tool"
    trusted = True

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [REFACTOR_ENGINE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(REFACTOR_ENGINE_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # RefactorEngineService Protocol Implementation
    # -------------------------------------------------------------------------

    def find_unused_functions(self, code: str) -> UnusedFunctionsResult:
        res = find_unused_functions(code=code)
        return UnusedFunctionsResult(
            status=res["status"],
            total_functions=res.get("total_functions", 0),
            unused_count=res.get("unused_count", 0),
            unused_functions=res.get("unused_functions", []),
            error=res.get("error"),
        )

    def extract_function_preview(
        self,
        code: str,
        start_line: int,
        end_line: int,
        new_func_name: str,
    ) -> FunctionExtractResult:
        res = extract_function_preview(
            code=code,
            start_line=start_line,
            end_line=end_line,
            new_func_name=new_func_name,
        )
        return FunctionExtractResult(
            status=res["status"],
            new_function_name=res.get("new_function_name", new_func_name),
            extracted_lines_count=res.get("extracted_lines_count", 0),
            function_definition=res.get("function_definition", ""),
            refactored_preview=res.get("refactored_preview", ""),
            error=res.get("error"),
        )
