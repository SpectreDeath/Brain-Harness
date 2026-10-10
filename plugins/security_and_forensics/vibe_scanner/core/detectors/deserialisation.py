"""Unsafe deserialisation detector (pickle, marshal, yaml.load)."""

from __future__ import annotations

import ast
from typing import List

from plugins.security_and_forensics.vibe_scanner.core.base import BaseDetector
from plugins.security_and_forensics.vibe_scanner.core.models import Finding


class UnsafeDeserialiseDetector(BaseDetector):
    """
    Detects pickle, yaml.load, marshal — classic AI blind spots.
    The multiplayer snake game used pickle for network data.
    AI tools use pickle because it's convenient and common in training data.
    """
    NAME = "UnsafeDeserialise"
    SEVERITY = "CRITICAL"

    UNSAFE_CALLS = {
        "pickle.loads": (
            "pickle.loads() executes arbitrary Python code. "
            "Any attacker who can control the input can achieve RCE."
        ),
        "pickle.load": (
            "pickle.load() from an untrusted file or socket enables RCE. "
            "AI tools use pickle for convenience — it is never safe with external data."
        ),
        "marshal.loads": (
            "marshal.loads() is as dangerous as pickle — arbitrary code execution."
        ),
        "yaml.load": (
            "yaml.load() without Loader=yaml.SafeLoader executes arbitrary Python. "
            "AI tools almost never add the SafeLoader argument."
        ),
        "__reduce__": (
            "__reduce__ defined on a class — enables arbitrary code execution "
            "when the object is unpickled."
        ),
    }

    def detect(self, tree: ast.AST, source: str, path: str) -> List[Finding]:
        findings: List[Finding] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            call_str = ast.unparse(node.func) if hasattr(ast, "unparse") else ""

            for pattern, detail in self.UNSAFE_CALLS.items():
                if pattern in call_str:
                    # yaml.load — check if SafeLoader is present
                    if pattern == "yaml.load":
                        args_str = ast.unparse(node) if hasattr(ast, "unparse") else ""
                        if "SafeLoader" in args_str or "safe_load" in args_str:
                            continue

                    findings.append(self._finding(
                        path=path,
                        line=node.lineno,
                        title=f"Unsafe deserialisation: {pattern}()",
                        detail=detail,
                        source=source,
                        fix_hint=(
                            "For pickle: use JSON instead.\n"
                            "For yaml: use yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader).\n"
                            "For marshal: use json or struct instead."
                        ),
                    ))
                    break

        return findings


__all__ = ["UnsafeDeserialiseDetector"]
