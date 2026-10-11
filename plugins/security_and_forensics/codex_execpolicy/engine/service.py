"""Typed service for deterministic execution policy and sandbox analysis."""

from __future__ import annotations

import sys
from typing import Any

from harness.services.kimi_bridge import BashAstNode
from plugins.security_and_forensics.codex_execpolicy.engine.ast_parser import (
    parse_bash_ast,
    tokenize_shell_ast,
)
from plugins.security_and_forensics.codex_execpolicy.engine.evaluator import (
    amend_prefix_rule,
    evaluate_command_policy,
)
from plugins.security_and_forensics.codex_execpolicy.engine.sandbox import (
    check_sandbox_requirements,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class CodexExecPolicyService:
    """Typed service for deterministic execution policy and sandbox analysis."""

    def evaluate(self, command: str) -> dict[str, Any]:
        """Evaluate a shell command against execution security policies."""
        return evaluate_command_policy(command)

    def amend(self, pattern: str, action: str, comment: str = "") -> dict[str, Any]:
        """Amend or insert a command prefix policy rule."""
        return amend_prefix_rule(pattern, action, comment)

    def tokenize(self, command: str) -> dict[str, Any]:
        """Tokenize a command string into structured AST representations."""
        return tokenize_shell_ast(command)

    def parse_ast(self, command: str) -> BashAstNode:
        """Parse command string into hierarchical BashAstNode tree."""
        return parse_bash_ast(command)

    def check_sandbox(self, command: str) -> dict[str, Any]:
        """Evaluate platform sandboxing requirements."""
        return check_sandbox_requirements(command)


__all__ = [
    "CodexExecPolicyService",
]
