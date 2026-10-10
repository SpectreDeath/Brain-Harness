"""SQL injection via string formatting detector."""

from __future__ import annotations

import ast
import re
from typing import List

from plugins.security_and_forensics.vibe_scanner.core.base import BaseDetector
from plugins.security_and_forensics.vibe_scanner.core.models import Finding


class SQLInjectionDetector(BaseDetector):
    """
    Detects string-formatted SQL queries.
    AI tools generate f-string and %-formatted queries
    because that pattern dominates their training data.
    """
    NAME = "SQLInjection"
    SEVERITY = "CRITICAL"

    # SQL keywords that suggest a query
    SQL_KEYWORDS = [
        "SELECT", "INSERT", "UPDATE", "DELETE",
        "DROP", "CREATE", "ALTER", "EXEC",
        "select", "insert", "update", "delete",
    ]

    # Formatting patterns that indicate injection risk
    INJECTION_PATTERNS = [
        r'f["\'].*SELECT.*\{',
        r'f["\'].*INSERT.*\{',
        r'f["\'].*UPDATE.*\{',
        r'f["\'].*DELETE.*\{',
        r'".*SELECT.*"\s*%\s*',
        r'".*INSERT.*"\s*%\s*',
        r'".*UPDATE.*"\s*%\s*',
        r'".*DELETE.*"\s*%\s*',
        r'\.format\(.*\).*(?:SELECT|INSERT|UPDATE|DELETE)',
        r'(?:SELECT|INSERT|UPDATE|DELETE).*\.format\(',
        r'(?:SELECT|INSERT|UPDATE|DELETE).*f["\']',
        r'query\s*[+=]\s*.*\+.*(?:user|input|param|data|name|id)',
        r'sql\s*[+=]\s*.*\+.*(?:user|input|param|data|name|id)',
    ]

    def detect(self, tree: ast.AST, source: str, path: str) -> List[Finding]:
        findings: List[Finding] = []
        lines = source.splitlines()

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            for pattern in self.INJECTION_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(self._finding(
                        path=path,
                        line=i,
                        title="SQL injection via string formatting",
                        detail=(
                            "SQL query constructed using string formatting (f-string, %, .format). "
                            "AI tools generate this pattern because it's common in training data. "
                            "Any user-controlled value in the query enables SQL injection."
                        ),
                        source=source,
                        fix_hint=(
                            "Use parameterised queries:\n"
                            "  cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))\n"
                            "Never concatenate or format user input into SQL."
                        ),
                    ))
                    break

        return findings


__all__ = ["SQLInjectionDetector"]
