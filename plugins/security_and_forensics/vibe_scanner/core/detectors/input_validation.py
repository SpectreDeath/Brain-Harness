"""Input validation vulnerability detector targeting dangerous sinks."""

from __future__ import annotations

import ast
from typing import Dict, List

from plugins.security_and_forensics.vibe_scanner.core.base import BaseDetector
from plugins.security_and_forensics.vibe_scanner.core.models import Finding


class InputValidationDetector(BaseDetector):
    """
    Detects user input used directly without validation.
    AI tools frequently skip length checks, type checks,
    and sanitisation — especially in Flask/FastAPI routes.
    """
    NAME = "InputValidation"
    SEVERITY = "HIGH"

    # Sources of untrusted input
    INPUT_SOURCES = {
        "request.json", "request.form", "request.args",
        "request.data", "request.get_json",
        "sys.argv", "input", "os.environ.get",
    }

    # Sinks that are dangerous without validation
    DANGEROUS_SINKS = {
        "open", "exec", "eval", "subprocess.run",
        "subprocess.call", "os.system", "os.popen",
        "cursor.execute", "conn.execute", "db.execute",
    }

    def detect(self, tree: ast.AST, source: str, path: str) -> List[Finding]:
        findings: List[Finding] = []

        # Track variables assigned from input sources
        input_vars: Dict[str, int] = {}  # var_name → line

        for node in ast.walk(tree):
            # Assignment: x = request.json.get("field")
            if isinstance(node, ast.Assign):
                if self._is_input_source(node.value):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            input_vars[target.id] = node.lineno

            # Direct call with input variable as argument
            if isinstance(node, ast.Call):
                func_name = self._func_name(node.func)
                if func_name in self.DANGEROUS_SINKS:
                    for arg in node.args:
                        if isinstance(arg, ast.Name) and arg.id in input_vars:
                            findings.append(self._finding(
                                path=path,
                                line=node.lineno,
                                title="Unvalidated input passed to dangerous sink",
                                detail=(
                                    f"Variable '{arg.id}' from user input "
                                    f"(line {input_vars[arg.id]}) passed directly "
                                    f"to '{func_name}' without validation."
                                ),
                                source=source,
                                fix_hint=(
                                    f"Validate '{arg.id}' before use: "
                                    f"check type, length, and allowed values."
                                ),
                            ))

        # Pattern: dict subscript used directly in sink (request.json["key"])
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._func_name(node.func)
                if func_name in self.DANGEROUS_SINKS:
                    for arg in node.args:
                        if self._is_input_source(arg):
                            findings.append(self._finding(
                                path=path,
                                line=node.lineno,
                                title="Raw user input passed to dangerous sink",
                                detail=(
                                    f"User input passed directly to '{func_name}' "
                                    f"with no intermediate validation."
                                ),
                                source=source,
                                fix_hint="Always validate and sanitise user input before passing to system calls.",
                            ))

        return findings

    def _is_input_source(self, node: ast.AST) -> bool:
        src = ast.unparse(node) if hasattr(ast, "unparse") else ""
        return any(s in src for s in self.INPUT_SOURCES)

    def _func_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._func_name(node.value)}.{node.attr}"
        return ""


__all__ = ["InputValidationDetector"]
