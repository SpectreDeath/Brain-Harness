"""Evaluator, Critic, and Safety Gatekeeper plugin for Brain Harness."""

from __future__ import annotations

import ast
import json
import re
from typing import Any

# Dangerous shell patterns
_DANGEROUS_PATTERNS = [
    (r"\brm\s+-[rfRF]{1,4}\s+[/~]", "Recursive root or home directory removal"),
    (r"\brm\s+-[rfRF]{1,4}\s+\*", "Wildcard file deletion"),
    (r"\bdel\s+/[fFqQsS]{1,4}\s+[cC]:\\", "System drive deletion"),
    (r"\bformat\s+[a-zA-Z]:", "Disk format operation"),
    (r"\bgit\s+reset\s+--hard\b", "Destructive hard git reset (discards all uncommitted work)"),
    (r"\bgit\s+clean\s+-[fFxd]{1,4}\b", "Forced git directory purge"),
    (r"\bgit\s+push\s+.*--force\b", "Forced git push (overwrites remote commit history)"),
    (r"\bdrop\s+(database|schema|table)\b", "Database object destruction"),
    (r"\bdd\s+if=.*of=/dev/[a-z]+", "Raw disk block overwrite"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb definition"),
    (r"\b(shutdown|reboot|init\s+0|halt)\b", "System termination command"),
]


def critic_check_safety(command: str) -> dict[str, Any]:
    """Scan a shell command for dangerous, destructive, or irreversible operations."""
    cleaned = command.strip()
    violations: list[str] = []

    for pattern, description in _DANGEROUS_PATTERNS:
        if re.search(pattern, cleaned, flags=re.IGNORECASE):
            violations.append(description)

    is_safe = len(violations) == 0
    risk_level = "low"
    if violations:
        risk_level = "critical" if any("destruction" in v or "removal" in v or "overwrite" in v for v in violations) else "high"

    return {
        "status": "ok",
        "command": command,
        "is_safe": is_safe,
        "risk_level": risk_level,
        "violations_count": len(violations),
        "violations": violations,
    }


def critic_evaluate_code(code: str, language: str = "python") -> dict[str, Any]:
    """Statically analyze code syntax, metrics, and safety anti-patterns."""
    lang = language.lower()

    if lang == "json":
        try:
            parsed = json.loads(code)
            return {
                "status": "ok",
                "language": "json",
                "valid": True,
                "score": 100,
                "type": type(parsed).__name__,
                "keys_count": len(parsed) if isinstance(parsed, dict) else len(parsed) if isinstance(parsed, list) else 1,
                "issues": [],
            }
        except Exception as e:
            return {
                "status": "ok",
                "language": "json",
                "valid": False,
                "score": 0,
                "issues": [f"JSON parse error: {e!s}"],
            }

    if lang != "python":
        # Basic heuristic analysis for other languages
        lines = code.splitlines()
        return {
            "status": "ok",
            "language": language,
            "valid": True,
            "lines_of_code": len(lines),
            "score": 85,
            "issues": [],
            "notes": ["AST analysis is only supported for Python and JSON."],
        }

    # Python AST static analysis
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {
            "status": "ok",
            "language": "python",
            "valid": False,
            "score": 0,
            "issues": [f"SyntaxError at line {e.lineno}, col {e.offset}: {e.msg}"],
        }

    lines = code.splitlines()
    loc = len(lines)
    functions: list[dict[str, Any]] = []
    classes: list[dict[str, Any]] = []
    anti_patterns: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            has_docstring = ast.get_docstring(node) is not None
            has_return_type = node.returns is not None
            functions.append({
                "name": node.name,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "args_count": len(node.args.args),
                "has_docstring": has_docstring,
                "has_return_type": has_return_type,
            })
            if not has_docstring:
                anti_patterns.append(f"Function '{node.name}' is missing a docstring.")
            if not has_return_type:
                anti_patterns.append(f"Function '{node.name}' is missing a return type annotation.")

        elif isinstance(node, ast.ClassDef):
            has_docstring = ast.get_docstring(node) is not None
            classes.append({
                "name": node.name,
                "methods_count": len([n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]),
                "has_docstring": has_docstring,
            })
            if not has_docstring:
                anti_patterns.append(f"Class '{node.name}' is missing a docstring.")

        elif isinstance(node, ast.Call):
            # Check for eval() or exec()
            if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                anti_patterns.append(f"Dangerous call to dynamic code evaluator '{node.func.id}()'.")

    # Calculate quality score (0 to 100)
    score = 100
    score -= min(40, len(anti_patterns) * 5)
    if loc > 300 and not classes and not functions:
        score -= 20
        anti_patterns.append("Monolithic script without modular functions or classes.")

    return {
        "status": "ok",
        "language": "python",
        "valid": True,
        "score": max(0, score),
        "metrics": {
            "lines_of_code": loc,
            "functions_count": len(functions),
            "classes_count": len(classes),
        },
        "functions": functions,
        "classes": classes,
        "issues": anti_patterns,
    }


def critic_review_plan(goal: str, steps: list[str]) -> dict[str, Any]:
    """Evaluate plan steps for completeness, verification, and risk mitigation."""
    if not steps:
        return {
            "status": "ok",
            "goal": goal,
            "score": 0,
            "feasible": False,
            "risks": ["Plan has no action steps defined."],
            "recommendations": ["Add sequential action steps to achieve the stated goal."],
        }

    risks: list[str] = []
    recommendations: list[str] = []
    has_verification = False
    has_backup_or_test = False

    for step in steps:
        s_lower = step.lower()
        if any(w in s_lower for w in ("verify", "test", "check", "validate", "assert", "inspect")):
            has_verification = True
        if any(w in s_lower for w in ("backup", "rollback", "fallback", "dry-run", "dry run")):
            has_backup_or_test = True

    if not has_verification:
        risks.append("No explicit verification, testing, or validation step in plan.")
        recommendations.append("Append an automated test or verification step at the end of the plan.")

    if len(steps) < 2:
        recommendations.append("Break the single monolithic step into atomic, testable sub-steps.")

    if len(steps) > 12:
        recommendations.append("Plan exceeds 12 steps; consider decomposing into sub-phases.")

    score = 100
    if not has_verification:
        score -= 25
    if not has_backup_or_test and any("delete" in s.lower() or "drop" in s.lower() or "replace" in s.lower() for s in steps):
        score -= 20
        risks.append("Destructive modifications planned without explicit backup/rollback precaution.")

    return {
        "status": "ok",
        "goal": goal,
        "total_steps": len(steps),
        "score": max(0, score),
        "feasible": score >= 50,
        "has_verification_step": has_verification,
        "risks": risks,
        "recommendations": recommendations,
    }
