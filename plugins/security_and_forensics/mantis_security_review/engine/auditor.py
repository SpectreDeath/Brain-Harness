"""Targeted security review formulation and static AST code auditing."""

from __future__ import annotations

import ast
import hashlib
import re
from typing import Any

from plugins.security_and_forensics.mantis_security_review.engine.db import compute_stable_signature


def plan_review(
    threat_model: dict[str, Any],
    target_paths: list[str],
    focus_cwe: list[str] | None = None,
) -> dict[str, Any]:
    """Formulate targeted security review plan."""
    focus_cwe = focus_cwe or ["CWE-20", "CWE-78", "CWE-89", "CWE-119", "CWE-416", "CWE-798"]
    tasks: list[dict[str, Any]] = []

    for path in target_paths:
        priority = (
            "high"
            if any(k in path.lower() for k in ["auth", "login", "admin", "sandbox", "crypto", "exec"])
            else "medium"
        )
        tasks.append({
            "target": path,
            "priority": priority,
            "recommended_cwe": focus_cwe,
            "strategy": "Static AST audit followed by false-positive review and crash reproducer generation.",
        })

    return {
        "status": "ok",
        "plan_id": f"plan_{hashlib.sha256(str(target_paths).encode()).hexdigest()[:8]}",
        "target_count": len(target_paths),
        "focus_cwe": focus_cwe,
        "tasks": tasks,
    }


def research_audit(
    target_file: str,
    code_content: str,
    focus_cwe: list[str] | None = None,
) -> dict[str, Any]:
    """Deep-dive static analysis audit of target source code."""
    findings: list[dict[str, Any]] = []
    lines = code_content.splitlines()

    # AST-level inspection for Python
    if target_file.endswith(".py"):
        try:
            tree = ast.parse(code_content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # eval / exec
                    if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                        sig = compute_stable_signature(target_file, "CWE-95", node.func.id)
                        findings.append({
                            "id": f"find_{sig[:8]}",
                            "filepath": target_file,
                            "line": node.lineno,
                            "cwe": "CWE-95",
                            "title": f"Arbitrary Code Execution via '{node.func.id}()'",
                            "severity": "critical",
                            "target_symbol": node.func.id,
                            "signature": sig,
                            "description": f"Direct invocation of {node.func.id}() evaluates dynamic code from input.",
                        })
                    # subprocess with shell=True
                    elif isinstance(node.func, ast.Attribute) and node.func.attr in ("Popen", "run", "call", "check_output"):
                        for kw in node.keywords:
                            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                sig = compute_stable_signature(target_file, "CWE-78", "subprocess_shell")
                                findings.append({
                                    "id": f"find_{sig[:8]}",
                                    "filepath": target_file,
                                    "line": node.lineno,
                                    "cwe": "CWE-78",
                                    "title": "OS Command Injection via subprocess(shell=True)",
                                    "severity": "critical",
                                    "target_symbol": "subprocess_shell",
                                    "signature": sig,
                                    "description": "Subprocess called with shell=True creates command injection risk.",
                                })
        except SyntaxError:
            pass

    # Regex heuristic sweeps
    for i, line in enumerate(lines, start=1):
        # Hardcoded keys
        if re.search(r"""(?i)(?:api_key|secret_key|private_key)\s*=\s*['"][a-zA-Z0-9_\-]{16,}['"]""", line):
            sig = compute_stable_signature(target_file, "CWE-798", f"line_{i}")
            findings.append({
                "id": f"find_{sig[:8]}",
                "filepath": target_file,
                "line": i,
                "cwe": "CWE-798",
                "title": "Hardcoded Cryptographic Secret/Key",
                "severity": "high",
                "target_symbol": f"line_{i}",
                "signature": sig,
                "description": f"Suspected hardcoded credential found on line {i}.",
            })
        # SQL Injection pattern
        if re.search(r"""(?i)(?:select|insert|update|delete)\s+.*\s+from\s+.*%\s*\(?""", line) or ("SELECT " in line.upper() and " + " in line):
            sig = compute_stable_signature(target_file, "CWE-89", f"line_{i}")
            findings.append({
                "id": f"find_{sig[:8]}",
                "filepath": target_file,
                "line": i,
                "cwe": "CWE-89",
                "title": "SQL Injection via String Concatenation/Interpolation",
                "severity": "high",
                "target_symbol": f"line_{i}",
                "signature": sig,
                "description": f"SQL query constructed using dynamic string formatting on line {i}.",
            })

    return {
        "status": "ok",
        "target_file": target_file,
        "findings_count": len(findings),
        "findings": findings,
    }
