"""Weak cryptography and insecure pseudo-randomness detector."""

from __future__ import annotations

import ast
import re
from typing import List

from plugins.security_and_forensics.vibe_scanner.core.base import BaseDetector
from plugins.security_and_forensics.vibe_scanner.core.models import Finding


class WeakCryptoDetector(BaseDetector):
    """
    Detects MD5/SHA1 used for security, random used for secrets.
    AI tools use these because they are common and simple —
    not because they are appropriate for security contexts.
    """
    NAME = "WeakCrypto"
    SEVERITY = "HIGH"

    # Weak hash functions when used for security (not checksums)
    WEAK_HASH_PATTERNS = [
        r'hashlib\.md5\s*\(',
        r'hashlib\.sha1\s*\(',
        r'md5\s*\(',
        r'sha1\s*\(',
    ]

    # Insecure random for security purposes
    INSECURE_RANDOM_PATTERNS = [
        r'random\.random\s*\(',
        r'random\.randint\s*\(',
        r'random\.choice\s*\(',
        r'random\.shuffle\s*\(',
    ]

    # Context words that suggest security use
    SECURITY_CONTEXT = [
        'password', 'token', 'secret', 'key', 'salt',
        'auth', 'session', 'csrf', 'nonce', 'otp',
        'hash', 'sign', 'verify', 'credential',
    ]

    def detect(self, tree: ast.AST, source: str, path: str) -> List[Finding]:
        findings: List[Finding] = []
        lines = source.splitlines()

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            # Context window around the line
            ctx_start = max(0, i - 4)
            ctx_end = min(len(lines), i + 2)
            context = " ".join(lines[ctx_start:ctx_end]).lower()

            in_security_context = any(w in context for w in self.SECURITY_CONTEXT)

            has_weak_hash = any(re.search(p, line) for p in self.WEAK_HASH_PATTERNS)
            has_insecure_random = in_security_context and any(
                re.search(p, line) for p in self.INSECURE_RANDOM_PATTERNS
            )

            if has_weak_hash and has_insecure_random:
                # Both issues on same line — emit a single merged finding
                findings.append(self._finding(
                    path=path,
                    line=i,
                    title="Weak crypto: MD5 + insecure random combined",
                    detail=(
                        "Two cryptographic weaknesses on the same line: "
                        "(1) MD5/SHA1 are cryptographically broken and must not be used for "
                        "passwords, tokens, or signatures. "
                        "(2) Python's random module is not cryptographically secure — "
                        "tokens generated this way are predictable and brute-forceable."
                    ),
                    source=source,
                    severity="CRITICAL",
                    fix_hint=(
                        "Replace both:\n"
                        "  import secrets, hashlib\n"
                        "  token = secrets.token_urlsafe(32)          # secure token\n"
                        "  h = hashlib.sha256(password.encode()).hexdigest()  # secure hash\n"
                        "For passwords use bcrypt, argon2, or scrypt."
                    ),
                ))
                continue

            # Weak hash only
            if has_weak_hash:
                findings.append(self._finding(
                    path=path,
                    line=i,
                    title="Weak hash function for security use",
                    detail=(
                        "MD5 and SHA1 are cryptographically broken. "
                        "AI tools use them because they are common in training data. "
                        "They should never be used for passwords, signatures, or tokens."
                    ),
                    source=source,
                    severity="HIGH" if in_security_context else "MEDIUM",
                    fix_hint=(
                        "For passwords: use bcrypt, argon2, or scrypt.\n"
                        "For tokens/signatures: use hashlib.sha256() or SHA3-256.\n"
                        "For checksums only: MD5/SHA1 are acceptable."
                    ),
                ))

            # Insecure random only
            if has_insecure_random:
                findings.append(self._finding(
                    path=path,
                    line=i,
                    title="Insecure random used in security context",
                    detail=(
                        "Python's random module is not cryptographically secure. "
                        "AI tools use it for convenience. "
                        "Tokens, session IDs, and salts generated this way are predictable."
                    ),
                    source=source,
                    severity="CRITICAL",
                    fix_hint=(
                        "Use secrets module instead:\n"
                        "  import secrets\n"
                        "  token = secrets.token_urlsafe(32)\n"
                        "  salt = secrets.token_bytes(16)"
                    ),
                ))

        return findings


__all__ = ["WeakCryptoDetector"]
