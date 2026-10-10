"""Silent exception swallowing and empty handler detector."""

from __future__ import annotations

import ast
from typing import List

from plugins.security_and_forensics.vibe_scanner.core.base import BaseDetector
from plugins.security_and_forensics.vibe_scanner.core.models import Finding


class ExceptionSwallowedDetector(BaseDetector):
    """
    Detects bare excepts and swallowed exceptions.
    AI tools generate try/except blocks that catch everything
    and do nothing — masking real failures silently in production.
    """
    NAME = "ExceptionSwallowed"
    SEVERITY = "HIGH"

    def detect(self, tree: ast.AST, source: str, path: str) -> List[Finding]:
        findings: List[Finding] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue

            # Bare except: (catches everything including KeyboardInterrupt)
            if node.type is None:
                findings.append(self._finding(
                    path=path,
                    line=node.lineno,
                    title="Bare except catches everything silently",
                    detail=(
                        "A bare 'except:' catches ALL exceptions including "
                        "KeyboardInterrupt and SystemExit. "
                        "AI tools generate this pattern when uncertain what might fail."
                    ),
                    source=source,
                    severity="HIGH",
                    fix_hint="Replace with 'except Exception as e:' and log or re-raise.",
                ))
                continue

            # except Exception with empty body or only pass/...
            body = node.body
            is_silent = all(
                isinstance(stmt, (ast.Pass, ast.Expr)) and (
                    isinstance(stmt, ast.Pass) or
                    (isinstance(stmt.value, ast.Constant) and
                     stmt.value.value is ...)
                )
                for stmt in body
            )

            if is_silent:
                exc_name = ast.unparse(node.type) if hasattr(ast, "unparse") else "Exception"
                findings.append(self._finding(
                    path=path,
                    line=node.lineno,
                    title=f"Exception '{exc_name}' swallowed silently",
                    detail=(
                        f"Caught '{exc_name}' but the handler is empty (pass/...). "
                        "The failure disappears. Production systems fail silently "
                        "for minutes or hours before anyone notices."
                    ),
                    source=source,
                    severity="HIGH",
                    fix_hint="At minimum: log the exception. Better: re-raise or return an error.",
                ))
                continue

            # except with only a comment or logger.debug (too quiet)
            has_only_debug = all(
                isinstance(stmt, ast.Expr) and
                isinstance(stmt.value, ast.Call) and
                isinstance(stmt.value.func, ast.Attribute) and
                stmt.value.func.attr in ("debug",)
                for stmt in body
                if not isinstance(stmt, ast.Pass)
            )

            if has_only_debug and len(body) <= 2:
                findings.append(self._finding(
                    path=path,
                    line=node.lineno,
                    title="Exception logged at DEBUG level only — invisible in production",
                    detail=(
                        "Exception is caught and logged at DEBUG level. "
                        "Production logging is typically INFO or WARNING — "
                        "this failure will be invisible."
                    ),
                    source=source,
                    severity="MEDIUM",
                    fix_hint="Use logger.warning() or logger.error() for exception handlers.",
                ))

        return findings


__all__ = ["ExceptionSwallowedDetector"]
