"""Domain models for Ebbinghaus Memory Decay Engine (Rule 12)."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


@dataclass(slots=True, frozen=True)
class MemoryNode:
    """Slotted immutable representation of a turn-tracked memory item."""

    node_id: str
    content: str
    category: str
    stability: float
    recall_count: int
    created_turn: int
    last_accessed_turn: int
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("node_id must be non-empty")
        if self.stability <= 0.0:
            raise ValueError("stability must be positive")
        if self.recall_count < 1:
            raise ValueError("recall_count must be at least 1")
        if self.created_turn < 0 or self.last_accessed_turn < 0:
            raise ValueError("turns must be non-negative")
        if self.last_accessed_turn < self.created_turn:
            raise ValueError("last_accessed_turn cannot be prior to created_turn")


@dataclass(slots=True, frozen=True)
class DecayConfig:
    """Configuration governing retention curves and eviction thresholds."""

    half_life_turns: int = 20
    stability_boost_alpha: float = 0.5
    retention_threshold: float = 0.35
    max_nodes: int = 256
    reinforcement_mode: str = "logarithmic"

    def __post_init__(self) -> None:
        if self.half_life_turns <= 0:
            raise ValueError("half_life_turns must be positive")
        if not (0.0 < self.retention_threshold < 1.0):
            raise ValueError("retention_threshold must be in (0, 1)")
        if self.stability_boost_alpha < 0.0:
            raise ValueError("stability_boost_alpha must be non-negative")
        if self.max_nodes <= 0:
            raise ValueError("max_nodes must be positive")


@dataclass(slots=True, frozen=True)
class EvictionDecision:
    """Outcome report of a memory evaluation pass."""

    evicted_ids: tuple[str, ...]
    retained_ids: tuple[str, ...]
    retention_scores: tuple[tuple[str, float], ...]
    elapsed_ms: float

    def __post_init__(self) -> None:
        if self.elapsed_ms < 0.0:
            raise ValueError("elapsed_ms must be non-negative")
