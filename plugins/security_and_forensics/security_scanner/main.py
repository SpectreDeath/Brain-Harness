"""Security Scanner plugin — secrets detection, AST vulnerability scan, and dependency audit."""

from __future__ import annotations

import ast
import re
from typing import Any

# Regex patterns for credential and secret leakage
_SECRET_PATTERNS: list[tuple[str, str, str]] = [
    ("AWS Access Key", r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}", "critical"),
    ("OpenAI / Generic API Key", r"sk-[a-zA-Z0-9_-]{32,}", "critical"),
    ("GitHub Token", r"(?:ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36,}", "critical"),
    ("Private Key", r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", "critical"),
    ("Slack Webhook", r"https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+", "high"),
    ("Generic Password in assignment", r"""(?i)(?:password|passwd|secret|api_key|token)\s*=\s*['"][^'"]{6,}['"]""", "medium"),
]


def scan_secrets(content: str) -> dict[str, Any]:
    """Scan string content for exposed secrets, tokens, and credentials."""
    findings: list[dict[str, Any]] = []
    lines = content.splitlines()

    for line_num, line in enumerate(lines, start=1):
        for name, pattern, severity in _SECRET_PATTERNS:
            for match in re.finditer(pattern, line):
                matched_val = match.group(0)
                # Mask secret
                if len(matched_val) > 8:
                    masked = matched_val[:3] + "..." + matched_val[-3:]
                else:
                    masked = "***"

                findings.append({
                    "rule": name,
                    "severity": severity,
                    "line": line_num,
                    "match_masked": masked,
                })

    return {
        "status": "ok",
        "secrets_found_count": len(findings),
        "clean": len(findings) == 0,
        "findings": findings,
    }


def scan_code_vulnerabilities(code: str) -> dict[str, Any]:
    """Analyze Python code for dangerous AST constructs (eval, exec, subprocess, yaml, pickle)."""
    issues: list[dict[str, Any]] = []

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"status": "error", "error": f"Python syntax error: {e!s}"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check eval() / exec()
            if isinstance(node.func, ast.Name):
                if node.func.id in ("eval", "exec"):
                    issues.append({
                        "type": "Code Injection",
                        "severity": "critical",
                        "line": node.lineno,
                        "description": f"Use of built-in '{node.func.id}()' can lead to arbitrary code execution.",
                    })
                elif node.func.id == "input":
                    issues.append({
                        "type": "Interactive Input",
                        "severity": "low",
                        "line": node.lineno,
                        "description": "Blocking input() call in headless agent environment.",
                    })

            # Check pickle.loads / yaml.load / os.system
            elif isinstance(node.func, ast.Attribute):
                attr_name = node.func.attr
                if isinstance(node.func.value, ast.Name):
                    mod_name = node.func.value.id
                    if mod_name == "pickle" and attr_name in ("loads", "load"):
                        issues.append({
                            "type": "Insecure Deserialization",
                            "severity": "critical",
                            "line": node.lineno,
                            "description": "Insecure deserialization via pickle allows remote code execution.",
                        })
                    elif mod_name in ("os", "subprocess") and attr_name in ("system", "popen", "check_output", "run"):
                        issues.append({
                            "type": "Command Execution",
                            "severity": "high",
                            "line": node.lineno,
                            "description": f"Shell invocation via {mod_name}.{attr_name}(). Ensure arguments are sanitized.",
                        })

    return {
        "status": "ok",
        "issues_count": len(issues),
        "safe": len(issues) == 0,
        "issues": issues,
    }


def audit_dependencies(requirements_content: str) -> dict[str, Any]:
    """Audit requirements.txt for unpinned versions or vulnerable packages."""
    unpinned: list[str] = []
    vulnerable_alerts: list[dict[str, Any]] = []

    lines = requirements_content.splitlines()
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if "==" not in line and ">=" not in line and "<=" not in line and "~=" not in line:
            unpinned.append(line)

        pkg_lower = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].strip().lower()
        if pkg_lower in ("pickle", "telnetlib", "pycrypto"):
            vulnerable_alerts.append({
                "package": pkg_lower,
                "severity": "high",
                "reason": f"Deprecated or security-sensitive package '{pkg_lower}' detected.",
            })

    return {
        "status": "ok",
        "total_rules_checked": len(lines),
        "unpinned_packages_count": len(unpinned),
        "unpinned_packages": unpinned,
        "vulnerabilities": vulnerable_alerts,
        "passed": len(vulnerable_alerts) == 0,
    }
