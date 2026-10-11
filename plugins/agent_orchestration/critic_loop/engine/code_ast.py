"""AST static analysis, language validation, and anti-pattern detection (Rule 42)."""

from __future__ import annotations

import ast
import json
import sys
from typing import Any

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def evaluate_code_ast(code: str, language: str = "python") -> dict[str, Any]:
    """Statically inspect syntax, AST complexity, and anti-patterns."""
    lang = language.lower()

    if lang == "json":
        try:
            parsed = json.loads(code)
            keys_count = (
                len(parsed)
                if isinstance(parsed, (dict, list))
                else 1
            )
            return {
                "status": "ok",
                "language": "json",
                "valid": True,
                "score": 100,
                "type": type(parsed).__name__,
                "keys_count": keys_count,
                "issues": [],
            }
        except json.JSONDecodeError as exc:
            return {
                "status": "error",
                "language": "json",
                "valid": False,
                "score": 0,
                "error": str(exc),
                "issues": [f"Invalid JSON syntax at line {exc.lineno}, column {exc.colno}"],
            }

    if lang != "python":
        return {
            "status": "ok",
            "language": lang,
            "valid": True,
            "score": 100,
            "message": f"Syntax parsing not supported for language '{language}', skipped.",
            "issues": [],
        }

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {
            "status": "error",
            "language": "python",
            "valid": False,
            "score": 0,
            "syntax_error": {
                "line": exc.lineno,
                "offset": exc.offset,
                "message": str(exc.msg),
                "text": exc.text,
            },
            "issues": [f"SyntaxError on line {exc.lineno}: {exc.msg}"],
        }

    functions: list[dict[str, Any]] = []
    classes: list[dict[str, Any]] = []
    anti_patterns: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node)
            arg_count = len(node.args.args)
            has_return = node.returns is not None

            functions.append({
                "name": node.name,
                "line": node.lineno,
                "args_count": arg_count,
                "has_docstring": docstring is not None,
                "has_return_type": has_return,
            })
            if arg_count > 7:
                anti_patterns.append(f"Function '{node.name}' has {arg_count} arguments (exceeds recommended max 7).")
            if docstring is None and not node.name.startswith("_"):
                anti_patterns.append(f"Function '{node.name}' lacks a docstring.")
            if not has_return and not node.name.startswith("_"):
                anti_patterns.append(f"Function '{node.name}' lacks a return type annotation.")

        elif isinstance(node, ast.ClassDef):
            classes.append({
                "name": node.name,
                "line": node.lineno,
                "has_docstring": ast.get_docstring(node) is not None,
            })

        elif isinstance(node, ast.ExceptHandler):
            if node.type is None:
                anti_patterns.append(
                    f"Bare 'except:' handler detected at line {node.lineno} (catches SystemExit/KeyboardInterrupt)."
                )

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "eval":
                anti_patterns.append(f"Use of 'eval()' detected at line {node.lineno} (security risk).")
            elif isinstance(node.func, ast.Name) and node.func.id == "exec":
                anti_patterns.append(f"Use of 'exec()' detected at line {node.lineno} (security risk).")

    loc = len([ln for ln in code.splitlines() if ln.strip() and not ln.strip().startswith("#")])
    score = max(0, 100 - len(anti_patterns) * 15) if anti_patterns else 100

    return {
        "status": "ok",
        "language": "python",
        "valid": True,
        "score": score,
        "metrics": {
            "lines_of_code": loc,
            "functions_count": len(functions),
            "classes_count": len(classes),
        },
        "functions": functions,
        "classes": classes,
        "issues": anti_patterns,
    }


__all__ = ["evaluate_code_ast"]
