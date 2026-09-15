"""Claude Code Bridge Service protocol, slotted/frozen data models, and ServiceKey."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from harness.kernel.context import ServiceKey


@dataclass(slots=True, frozen=True)
class BashGuardrailResult:
    """Evaluation record of a proposed shell command against safety guardrails (Rule 12)."""

    command: str
    is_dangerous: bool
    risk_level: str  # "safe", "medium", "blocked"
    reason: str | None = None
    status: str = "ok"

    def __post_init__(self) -> None:
        assert self.risk_level in ("safe", "medium", "blocked"), f"Invalid risk level: {self.risk_level}"


@dataclass(slots=True, frozen=True)
class PromptCompactionResult:
    """Evaluation record of context prompt compression (Rule 12)."""

    original_length: int
    compacted_length: int
    compacted_text: str
    reduction_pct: float
    status: str = "ok"

    def __post_init__(self) -> None:
        assert self.reduction_pct >= 0.0, f"Negative reduction_pct: {self.reduction_pct}"


@runtime_checkable
class ClaudeCodeBridgeService(Protocol):
    """Protocol for Claude Code pre-tool guardrails, prompt compaction, and session telemetry."""

    def evaluate_bash_guardrails(self, command: str) -> BashGuardrailResult:
        """Inspect a shell command line before execution against dangerous patterns."""
        ...

    def compact_prompt(self, text: str, max_lines: int = 50) -> PromptCompactionResult:
        """Compact context prompt using deduplication and progressive line folding."""
        ...


CLAUDE_CODE_BRIDGE_KEY: ServiceKey[ClaudeCodeBridgeService] = ServiceKey("service.claude_code_bridge")
