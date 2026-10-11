"""Deterministic AST-Level Shell Command Execution Policy & Sandbox Resolution Plugin.

Ported from OpenAI Codex (`codex-rs/execpolicy` and `codex-rs/sandboxing`) and enhanced
with pure-language recursive Tree-Sitter Bash AST decompilation from Kimi Code.
Provides deterministic AST parsing, subshell extraction, prefix rule matching, approval elevation,
and platform-native sandbox requirement analysis for agent loops.
"""

from __future__ import annotations

import sys
from typing import Any
import structlog

from harness.kernel.context import ServiceContext
from harness.plugins.base import HarnessPlugin
from plugins.security_and_forensics.codex_execpolicy.engine import (
    EXEC_POLICY_KEY,
    AstToken,
    CodexExecPolicyService,
    PrefixRule,
    amend_prefix_rule,
    check_sandbox_requirements,
    evaluate_command_policy,
    get_active_rules,
    parse_bash_ast,
    reset_active_rules,
    tokenize_shell_ast,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = structlog.get_logger(__name__)


class CodexExecPolicyPlugin(HarnessPlugin):
    """Brain Harness Plugin exposing Codex deterministic execpolicy and sandbox analyzer."""

    name = "plugin.codex_execpolicy"
    version = "1.0.0"

    def __init__(self) -> None:
        super().__init__()
        self._service = CodexExecPolicyService()

    @property
    def provides(self) -> list[Any]:
        """Declared service keys provided by this plugin (Rule 3 & Rule 45)."""
        return [EXEC_POLICY_KEY]

    async def on_enable(self, context: ServiceContext) -> None:
        """Register typed service into IoC container on startup (Rule 1 & Rule 2)."""
        context.provide(EXEC_POLICY_KEY, self._service, provider=self.name)
        logger.info("CodexExecPolicyPlugin enabled and service registered")

    async def on_disable(self, context: ServiceContext) -> None:
        """Unregister service on shutdown."""
        logger.info("CodexExecPolicyPlugin disabled")


# Plugin Module Singleton & IoC Provider Invariant (Rule 45)
plugin = CodexExecPolicyPlugin()

__all__ = [
    "EXEC_POLICY_KEY",
    "AstToken",
    "CodexExecPolicyPlugin",
    "CodexExecPolicyService",
    "PrefixRule",
    "amend_prefix_rule",
    "check_sandbox_requirements",
    "evaluate_command_policy",
    "get_active_rules",
    "parse_bash_ast",
    "plugin",
    "reset_active_rules",
    "tokenize_shell_ast",
]
