"""AST refactoring engine, unused function identifier, and function extractor plugin."""

from __future__ import annotations

import ast
from typing import Any


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
