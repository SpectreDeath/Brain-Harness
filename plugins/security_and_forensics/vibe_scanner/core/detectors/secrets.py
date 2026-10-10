"""Hardcoded secrets and credential leak detector."""

from __future__ import annotations

import ast
import re
from typing import List

from plugins.security_and_forensics.vibe_scanner.core.base import BaseDetector
from plugins.security_and_forensics.vibe_scanner.core.models import Finding


class HardcodedSecretDetector(BaseDetector):
    """
    Detects API keys, passwords, tokens hardcoded in source.
    AI tools frequently generate working examples with real-looking
    secrets — and developers ship them without noticing.
    Secret leakage is 6.4% higher in AI-assisted repos.
    """
    NAME = "HardcodedSecret"
    SEVERITY = "CRITICAL"

    # Variable name patterns that suggest secrets
    SECRET_VAR_PATTERNS = [
        r'\b(api_key|apikey|api_token|access_token|secret_key|secret)\s*=',
        r'\b(password|passwd|pwd)\s*=',
        r'\b(private_key|signing_key|auth_token)\s*=',
        r'\b(aws_secret|stripe_key|openai_key|anthropic_key)\s*=',
        r'\b(database_password|db_password|db_pass)\s*=',
        r'\b(jwt_secret|session_secret|cookie_secret)\s*=',
    ]

    # Value patterns that look like real secrets (not env var lookups)
    REAL_SECRET_PATTERNS = [
        r'=\s*["\'][a-zA-Z0-9+/]{20,}["\']',   # long base64-ish strings
        r'=\s*["\']sk-[a-zA-Z0-9]{20,}["\']',   # OpenAI-style keys
        r'=\s*["\']pk_[a-zA-Z0-9]{20,}["\']',   # Stripe-style keys
        r'=\s*["\']ghp_[a-zA-Z0-9]{36}["\']',   # GitHub tokens
        r'=\s*["\'][A-Z0-9]{20,}["\']',          # AWS-style keys
    ]

    # Safe patterns (using env vars or config)
    SAFE_PATTERNS = [
        r'os\.environ',
        r'os\.getenv',
        r'getenv',
        r'environ\[',
        r'config\[',
        r'settings\.',
        r'None',
        r'""',
        r"''",
        r'your[_-]',
        r'xxx',
        r'placeholder',
        r'example',
        r'changeme',
        r'<',
        r'\$\{',
    ]

    def detect(self, tree: ast.AST, source: str, path: str) -> List[Finding]:
        findings: List[Finding] = []
        lines = source.splitlines()

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            # Skip function calls — secret vars are assignments, not call arguments.
            if re.search(r'\.\s*execute\s*\(', line):
                continue

            line_lower = line.lower()

            # Check for secret variable names
            has_secret_var = any(
                re.search(p, line_lower) for p in self.SECRET_VAR_PATTERNS
            )
            if not has_secret_var:
                continue

            # Check if value looks like a real secret (not env var)
            has_safe = any(re.search(p, line, re.IGNORECASE) for p in self.SAFE_PATTERNS)
            if has_safe:
                continue

            # Check if value is a non-empty string literal
            has_real_value = (
                re.search(r'=\s*["\'][^"\']{8,}["\']', line) or
                any(re.search(p, line) for p in self.REAL_SECRET_PATTERNS)
            )

            if has_real_value:
                findings.append(self._finding(
                    path=path,
                    line=i,
                    title="Hardcoded secret in source code",
                    detail=(
                        "A credential or secret appears to be hardcoded as a "
                        "string literal. AI tools generate working code with "
                        "placeholder secrets that developers forget to replace."
                    ),
                    source=source,
                    fix_hint=(
                        "Use environment variables: \n"
                        "  secret = os.environ.get('MY_SECRET')\n"
                        "Never commit secrets to version control."
                    ),
                ))

        return findings


__all__ = ["HardcodedSecretDetector"]
