"""Base detector class and snippet generation."""

from __future__ import annotations

import ast
from typing import List, Optional

from plugins.security_and_forensics.vibe_scanner.core.models import Finding

class BaseDetector:
    """All detectors inherit from this."""
    NAME: str = "base"
    SEVERITY: str = "MEDIUM"

    def detect(self, tree: ast.AST, source: str, path: str) -> List[Finding]:
        raise NotImplementedError

    def _snippet(self, source: str, line: int, context: int = 1) -> str:
        lines = source.splitlines()
        start = max(0, line - context - 1)
        end = min(len(lines), line + context)
        return "\n".join(
            f"{'→' if i == line - 1 else ' '} {i+1:4}  {lines[i]}"
            for i in range(start, end)
        )

    def _finding(
        self,
        path: str,
        line: int,
        title: str,
        detail: str,
        source: str,
        severity: str = None,
        fix_hint: str = "",
    ) -> Finding:
        return Finding(
            file=path,
            line=line,
            detector=self.NAME,
            severity=severity or self.SEVERITY,
            title=title,
            detail=detail,
            code_snippet=self._snippet(source, line),
            fix_hint=fix_hint,
        )


__all__ = ["BaseDetector"]
