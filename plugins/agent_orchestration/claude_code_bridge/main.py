"""Claude Code Bridge plugin providing pre-tool bash command guardrails and prompt compaction."""

from __future__ import annotations

import re
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.claude_code import (
    CLAUDE_CODE_BRIDGE_KEY,
    BashGuardrailResult,
    ClaudeCodeBridgeService,
    PromptCompactionResult,
)

logger = structlog.get_logger(__name__)

# Dangerous patterns derived from claude-code hooks and git-guardrails
DANGEROUS_PATTERNS = [
    (r"\bgit\s+push\s+.*(--force|-f)\b", "Destructive force push blocked"),
    (r"\bgit\s+reset\s+--hard\b", "Hard git reset blocked"),
    (r"\bgit\s+clean\s+.*(-f|-fd|-xdf)\b", "Destructive git clean blocked"),
    (r"\brm\s+-(rf|fr)\s+[/~]", "Root or home recursive deletion blocked"),
    (r"\bdd\s+if=.*of=/dev/[sh]d[a-z]", "Raw disk overwrite blocked"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb blocked"),
]


class ClaudeCodeBridgePlugin(HarnessPlugin, ClaudeCodeBridgeService):
    """Harness Plugin providing Claude Code pre-tool guardrails and prompt compaction."""

    name = "plugin.claude_code_bridge"
    version = "1.0.0"
    description = "Claude Code Bridge plugin for shell guardrails and prompt compaction"
    trusted = True

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [CLAUDE_CODE_BRIDGE_KEY]

    def on_load(self, context: ServiceContext) -> None:
        context.provide(CLAUDE_CODE_BRIDGE_KEY, self, provider=self.name)
        logger.info("ClaudeCodeBridgePlugin registered into IoC container")

    def on_unload(self, context: ServiceContext) -> None:
        logger.info("ClaudeCodeBridgePlugin unloaded")

    def evaluate_bash_guardrails(self, command: str) -> BashGuardrailResult:
        """Inspect a shell command line before execution against dangerous patterns."""
        cmd_stripped = command.strip()
        for pattern, reason in DANGEROUS_PATTERNS:
            if re.search(pattern, cmd_stripped, re.IGNORECASE):
                return BashGuardrailResult(
                    command=cmd_stripped,
                    is_dangerous=True,
                    risk_level="blocked",
                    reason=reason,
                    status="blocked",
                )

        # Medium risk check (e.g. git checkout -B or git branch -D)
        if re.search(r"\bgit\s+branch\s+-D\b", cmd_stripped, re.IGNORECASE):
            return BashGuardrailResult(
                command=cmd_stripped,
                is_dangerous=False,
                risk_level="medium",
                reason="Force branch deletion requires caution",
                status="ok",
            )

        return BashGuardrailResult(
            command=cmd_stripped,
            is_dangerous=False,
            risk_level="safe",
            reason=None,
            status="ok",
        )

    def compact_prompt(self, text: str, max_lines: int = 50) -> PromptCompactionResult:
        """Compact context prompt using deduplication and progressive line folding."""
        lines = text.splitlines()
        orig_len = len(text)

        # 1. Deduplicate consecutive identical lines
        deduped: list[str] = []
        for line in lines:
            if not deduped or line != deduped[-1]:
                deduped.append(line)

        # 2. Middle-out progressive folding if exceeding max_lines
        if len(deduped) > max_lines:
            half = (max_lines - 2) // 2
            omitted = len(deduped) - (half * 2)
            compacted_lines = (
                deduped[:half]
                + [f"... [{omitted} lines folded for context efficiency] ..."]
                + deduped[-half:]
            )
        else:
            compacted_lines = deduped

        compacted_text = "\n".join(compacted_lines)
        compacted_len = len(compacted_text)
        reduction_pct = round(max(0.0, (1.0 - (compacted_len / max(1, orig_len))) * 100.0), 2)

        return PromptCompactionResult(
            original_length=orig_len,
            compacted_length=compacted_len,
            compacted_text=compacted_text,
            reduction_pct=reduction_pct,
            status="ok",
        )


# Export authoritative module-level singleton (Rule 45)
plugin = ClaudeCodeBridgePlugin()
