"""Slotted and frozen domain models and token estimator for context optimization (Rule 12 & Rule 43)."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any

from harness.services.llm import LLMMessage

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


@dataclass(slots=True, frozen=True)
class ContextOptimizationConfig:
    """Slotted, frozen configuration knobs for agent context budgeting and compaction."""

    max_observation_chars: int = 4000
    max_total_messages: int = 30
    recent_messages_preserve: int = 6
    compact_json: bool = True
    enable_pruning: bool = True
    token_budget: int = 16000
    repo_map_root: str | None = None
    repo_map_budget_tokens: int = 1024

    def __post_init__(self) -> None:
        assert self.max_observation_chars > 0, "max_observation_chars must be positive"
        assert self.max_total_messages >= 2, "max_total_messages must be >= 2"
        assert self.recent_messages_preserve >= 1, "recent_messages_preserve must be >= 1"
        assert self.token_budget > 0, "token_budget must be positive"
        assert self.repo_map_budget_tokens >= 0, "repo_map_budget_tokens must be non-negative"

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_observation_chars": self.max_observation_chars,
            "max_total_messages": self.max_total_messages,
            "recent_messages_preserve": self.recent_messages_preserve,
            "compact_json": self.compact_json,
            "enable_pruning": self.enable_pruning,
            "token_budget": self.token_budget,
            "repo_map_root": self.repo_map_root,
            "repo_map_budget_tokens": self.repo_map_budget_tokens,
        }


@dataclass(slots=True, frozen=True)
class PruningMetric:
    """Diagnostic execution telemetry for a single pruning strategy pass."""

    strategy_name: str
    initial_count: int
    pruned_count: int
    estimated_tokens_before: int
    estimated_tokens_after: int
    duration_ms: float = 0.0

    def __post_init__(self) -> None:
        assert self.strategy_name, "strategy_name cannot be empty"
        assert self.initial_count >= 0, "initial_count must be non-negative"
        assert self.pruned_count >= 0, "pruned_count must be non-negative"

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy_name,
            "initial_messages": self.initial_count,
            "pruned_messages": self.pruned_count,
            "tokens_before": self.estimated_tokens_before,
            "tokens_after": self.estimated_tokens_after,
            "duration_ms": self.duration_ms,
        }


@dataclass(slots=True, frozen=True)
class ContextOptimizationResult:
    """Slotted, frozen evaluation result of a complete pre-LLM context optimization run."""

    status: str = "ok"
    messages: tuple[LLMMessage, ...] = field(default_factory=tuple)
    original_count: int = 0
    optimized_count: int = 0
    estimated_tokens: int = 0
    repo_map_injected: bool = False
    metrics: tuple[PruningMetric, ...] = field(default_factory=tuple)
    error: str | None = None

    def __post_init__(self) -> None:
        assert self.status in ("ok", "error"), f"Invalid status: {self.status}"
        assert self.original_count >= 0, "original_count must be non-negative"
        assert self.optimized_count >= 0, "optimized_count must be non-negative"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "original_count": self.original_count,
            "optimized_count": self.optimized_count,
            "estimated_tokens": self.estimated_tokens,
            "repo_map_injected": self.repo_map_injected,
            "metrics": [m.to_dict() for m in self.metrics],
            "error": self.error,
        }


def estimate_tokens(messages: list[LLMMessage] | tuple[LLMMessage, ...]) -> int:
    """Fast character-based heuristic token estimator (~4 chars per token)."""
    total_chars = sum(len(m.content or "") for m in messages)
    return max(1, total_chars // 4) if messages else 0


__all__ = [
    "ContextOptimizationConfig",
    "ContextOptimizationResult",
    "PruningMetric",
    "estimate_tokens",
]
