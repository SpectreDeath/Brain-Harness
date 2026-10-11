"""Deterministic AST-Level Shell Command Execution Policy & Sandbox Resolution Engine."""

from __future__ import annotations

import sys

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from plugins.security_and_forensics.codex_execpolicy.engine.ast_parser import (
    parse_bash_ast,
    tokenize_shell_ast,
)
from plugins.security_and_forensics.codex_execpolicy.engine.evaluator import (
    amend_prefix_rule,
    evaluate_command_policy,
    get_active_rules,
    reset_active_rules,
)
from plugins.security_and_forensics.codex_execpolicy.engine.models import (
    EXEC_POLICY_KEY,
    AstToken,
    PrefixRule,
)
from plugins.security_and_forensics.codex_execpolicy.engine.sandbox import (
    check_sandbox_requirements,
)
from plugins.security_and_forensics.codex_execpolicy.engine.service import (
    CodexExecPolicyService,
)

__all__ = [
    "EXEC_POLICY_KEY",
    "AstToken",
    "CodexExecPolicyService",
    "PrefixRule",
    "amend_prefix_rule",
    "check_sandbox_requirements",
    "evaluate_command_policy",
    "get_active_rules",
    "parse_bash_ast",
    "reset_active_rules",
    "tokenize_shell_ast",
]
