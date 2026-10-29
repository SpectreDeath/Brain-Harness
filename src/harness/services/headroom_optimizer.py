"""Headroom Context Optimizer service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable
import structlog

from harness.kernel.context import ServiceKey

logger = structlog.get_logger()


@dataclass(slots=True, frozen=True)
class ContentCompressResult:
    """Slotted immutable result of content compression."""

    status: str
    original_tokens: int
    compressed_tokens: int
    savings_ratio: float
    strategy: str
    compressed_text: str
    error: str | None = None

    def __post_init__(self) -> None:
        if self.status not in ("ok", "error", "skipped"):
            raise ValueError(f"Invalid status: {self.status}")
        if self.original_tokens < 0 or self.compressed_tokens < 0:
            raise ValueError("Token counts cannot be negative")
        if not (0.0 <= self.savings_ratio <= 1.0):
            raise ValueError(f"savings_ratio must be between 0.0 and 1.0, got {self.savings_ratio}")


@dataclass(slots=True, frozen=True)
class DedupTurnsResult:
    """Slotted immutable result of cross-turn deduplication (CCR)."""

    status: str
    compacted_messages: list[dict[str, Any]]
    deduplicated_blocks: int
    tokens_saved: int
    error: str | None = None

    def __post_init__(self) -> None:
        if self.status not in ("ok", "error"):
            raise ValueError(f"Invalid status: {self.status}")
        if self.deduplicated_blocks < 0 or self.tokens_saved < 0:
            raise ValueError("Counts cannot be negative")


@dataclass(slots=True, frozen=True)
class CacheDriftResult:
    """Slotted immutable result of cache alignment detector."""

    status: str
    is_cache_stable: bool
    volatile_items: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    error: str | None = None

    def __post_init__(self) -> None:
        if self.status not in ("ok", "error"):
            raise ValueError(f"Invalid status: {self.status}")


@dataclass(slots=True, frozen=True)
class ThinkingCompactResult:
    """Slotted immutable result of prior-turn extended thinking compaction."""

    status: str
    messages: list[dict[str, Any]]
    compacted_turns: int
    tokens_saved: int
    error: str | None = None

    def __post_init__(self) -> None:
        if self.status not in ("ok", "error"):
            raise ValueError(f"Invalid status: {self.status}")
        if self.compacted_turns < 0 or self.tokens_saved < 0:
            raise ValueError("Counts cannot be negative")


@dataclass(slots=True, frozen=True)
class SavingsLedger:
    """Slotted immutable savings ledger across active session."""

    total_in_tokens: int
    total_out_tokens: int
    net_tokens_saved: int
    net_cost_saved_usd: float
    strategy_counts: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.total_in_tokens < 0 or self.total_out_tokens < 0:
            raise ValueError("Tokens cannot be negative")
        if self.net_tokens_saved < 0:
            raise ValueError("net_tokens_saved cannot be negative")


@runtime_checkable
class HeadroomContextOptimizerService(Protocol):
    """Protocol for Headroom-based context optimization, routing, CCR, and cache alignment."""

    def compress_content(
        self,
        content: str,
        content_type: str | None = None,
        target_ratio: float = 0.6,
        preserve_keys: list[str] | None = None,
    ) -> ContentCompressResult:
        """Route and compress arbitrary content based on syntax/structure."""
        ...

    def dedup_turns(
        self,
        messages: list[dict[str, Any]],
        min_lines: int = 3,
        min_chars: int = 40,
    ) -> DedupTurnsResult:
        """Apply Cross-Context Retrieval (CCR) deduplication across conversation turns."""
        ...

    def detect_cache_drift(
        self,
        system_prompt: str,
    ) -> CacheDriftResult:
        """Inspect system prompt for volatile elements that invalidate prefix cache."""
        ...

    def compact_thinking(
        self,
        messages: list[dict[str, Any]],
        keep_last_turns: int = 2,
    ) -> ThinkingCompactResult:
        """Convert older thinking blocks into lightweight deterministic markers."""
        ...

    def get_savings_metrics(
        self,
        reset: bool = False,
    ) -> SavingsLedger:
        """Retrieve real-time cumulative savings metrics and token ledger."""
        ...


HEADROOM_CONTEXT_OPTIMIZER_KEY: ServiceKey[HeadroomContextOptimizerService] = ServiceKey(
    "memory.headroom_context_optimizer"
)
