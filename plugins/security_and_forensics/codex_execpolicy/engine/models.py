"""Slotted models, rules, and default security patterns for Codex ExecPolicy (Rule 12)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from harness.kernel.context import ServiceKey

if TYPE_CHECKING:
    from plugins.security_and_forensics.codex_execpolicy.engine.service import CodexExecPolicyService

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

EXEC_POLICY_KEY: ServiceKey[CodexExecPolicyService] = ServiceKey("security.codex_execpolicy")


@dataclass(slots=True)
class PrefixRule:
    """Deterministic command prefix rule (Rule 12)."""

    pattern: list[str]
    action: str  # "allow", "prompt", "deny"
    comment: str = ""
    is_regex: bool = False


@dataclass(slots=True, frozen=True)
class AstToken:
    """Structured AST token representing parsed shell command elements (Rule 12 & Rule 43)."""

    raw: str
    is_operator: bool = False
    is_redirection: bool = False
    is_variable: bool = False


# Default allowed prefix rules
_DEFAULT_ALLOW_PREFIXES: list[PrefixRule] = [
    PrefixRule(["git", "status"], "allow", "Safe git status query"),
    PrefixRule(["git", "diff"], "allow", "Safe git diff inspection"),
    PrefixRule(["git", "log"], "allow", "Safe git history inspection"),
    PrefixRule(["git", "branch"], "allow", "Safe git branch listing"),
    PrefixRule(["git", "rev-parse"], "allow", "Safe git commit resolution"),
    PrefixRule(["pytest"], "allow", "Test runner execution"),
    PrefixRule(["python", "-m", "pytest"], "allow", "Python pytest module execution"),
    PrefixRule(["python", "--version"], "allow", "Python version query"),
    PrefixRule(["python3", "--version"], "allow", "Python3 version query"),
    PrefixRule(["node", "--version"], "allow", "Node.js version query"),
    PrefixRule(["npm", "test"], "allow", "NPM test script"),
    PrefixRule(["npm", "run", "test"], "allow", "NPM test script"),
    PrefixRule(["cargo", "check"], "allow", "Cargo compiler check"),
    PrefixRule(["cargo", "test"], "allow", "Cargo test execution"),
    PrefixRule(["ls"], "allow", "Directory listing"),
    PrefixRule(["dir"], "allow", "Windows directory listing"),
    PrefixRule(["echo"], "allow", "Standard echo"),
    PrefixRule(["pwd"], "allow", "Print working directory"),
    PrefixRule(["whoami"], "allow", "User identity query"),
]

# Catastrophic danger patterns
_DEFAULT_DENY_PATTERNS: list[tuple[str, str, str]] = [
    (r"\brm\s+-[rR]f\s+(?:/|/\*|~|\$HOME)", "Catastrophic filesystem root deletion", "deny"),
    (r"\bmkfs(?:\.[a-z0-9]+)?\s+", "Filesystem format command", "deny"),
    (r"\bdd\s+if=.*of=/dev/[sh]d", "Direct disk overwrite with dd", "deny"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb denial of service", "deny"),
    (r"\b(?:curl|wget|fetch)\b.*\|\s*(?:bash|sh|zsh|python|perl|powershell)", "Unchecked remote script pipe execution", "prompt"),
    (r"\bchmod\s+(?:-R\s+)?777\b", "Dangerous open permission granting", "prompt"),
    (r"\bsudo\s+", "Privilege escalation request", "prompt"),
    (r"\bshutdown\s+", "System shutdown command", "deny"),
    (r"\breboot\s+", "System reboot command", "deny"),
]

__all__ = [
    "EXEC_POLICY_KEY",
    "AstToken",
    "PrefixRule",
    "_DEFAULT_ALLOW_PREFIXES",
    "_DEFAULT_DENY_PATTERNS",
]
