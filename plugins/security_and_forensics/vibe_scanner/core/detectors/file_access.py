"""Unsafe file access and path traversal detector."""

from __future__ import annotations

import ast
import re
from typing import List

from plugins.security_and_forensics.vibe_scanner.core.base import BaseDetector
from plugins.security_and_forensics.vibe_scanner.core.models import Finding


class UnsafeFileAccessDetector(BaseDetector):
    """
    Detects path traversal vulnerabilities and unchecked file ops.
    AI tools almost never add path.resolve() + .relative_to() checks.
    The Lovable breach and the rglob() incident both trace here.
    """
    NAME = "UnsafeFileAccess"
    SEVERITY = "CRITICAL"

    # Patterns that suggest user-controlled path input
    PATH_INPUT_PATTERNS = [
        r'request\.(json|form|args)',
        r'sys\.argv\[',
        r'\binput\s*\(',
        r'os\.environ\.get\s*\(',
        r'data\[[\'"]\w*[Pp]ath',
        r'data\[[\'"]\w*[Ff]ile',
        r'data\[[\'"]\w*[Nn]ame',
        r'params\[',
        r'query\[',
    ]

    # File operations that are dangerous with untrusted paths
    FILE_OPS = [
        r'\bopen\s*\(',
        r'Path\s*\(',
        r'pathlib\.Path\s*\(',
        r'os\.path\.(join|exists|isfile)',
        r'shutil\.(copy|move|rmtree)',
        r'os\.(remove|unlink|rename)',
        r'\.read_text\s*\(',
        r'\.write_text\s*\(',
        r'\.read_bytes\s*\(',
    ]

    # Safety patterns — if present nearby, it's likely safe
    SAFETY_PATTERNS = [
        r'\.resolve\(\)',
        r'\.relative_to\(',
        r'os\.path\.abspath',
        r'os\.path\.realpath',
        r'\.startswith\(',
        r'in ALLOWED_',
        r'allowlist',
        r'whitelist',
        r'secure_filename',
        r'safe_path\(',        # custom safe path helpers
        r'sanitize_path\(',
        r'validate_path\(',
        r'check_path\(',
    ]

    def detect(self, tree: ast.AST, source: str, path: str) -> List[Finding]:
        findings: List[Finding] = []
        lines = source.splitlines()

        # Track lines that contain user input sources
        input_lines: List[int] = []
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                continue
            if any(re.search(p, line) for p in self.PATH_INPUT_PATTERNS):
                input_lines.append(i)

        # For each line with a file op, check if input appeared nearby (within 10 lines)
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                continue

            has_file_op = any(re.search(p, line) for p in self.FILE_OPS)
            if not has_file_op:
                continue

            # Check if any input source appears within 10 lines before this line
            nearby_input = any(
                0 < (i - inp_line) <= 10
                for inp_line in input_lines
            ) or any(re.search(p, line) for p in self.PATH_INPUT_PATTERNS)

            if not nearby_input:
                continue

            # Check surrounding context for safety patterns
            context_start = max(0, i - 15)
            context_end = min(len(lines), i + 5)
            context = "\n".join(lines[context_start:context_end])

            has_safety = any(
                re.search(p, context) for p in self.SAFETY_PATTERNS
            )

            if not has_safety:
                findings.append(self._finding(
                    path=path,
                    line=i,
                    title="Unsafe file access with user-controlled path",
                    detail=(
                        "File operation uses a path derived from user input "
                        "with no path traversal protection. "
                        "An attacker can use '../../../etc/passwd' to escape the sandbox."
                    ),
                    source=source,
                    fix_hint=(
                        "Use: safe = Path(user_path).resolve()\n"
                        "Then: safe.relative_to(BASE_DIR)  # raises ValueError if outside"
                    ),
                ))

        # Detect rglob() with no depth limit — the rglob incident
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and
                        node.func.attr == "rglob"):
                    findings.append(self._finding(
                        path=path,
                        line=node.lineno,
                        title="Unbounded rglob() — performance and path risk",
                        detail=(
                            "rglob() scans recursively with no depth limit. "
                            "On large directories this hangs indefinitely. "
                            "AI tools use rglob() by default — it should be opt-in."
                        ),
                        source=source,
                        severity="MEDIUM",
                        fix_hint=(
                            "Replace rglob() with glob() for shallow search. "
                            "Add recursive=False as default, require explicit opt-in."
                        ),
                    ))

        return findings


__all__ = ["UnsafeFileAccessDetector"]
