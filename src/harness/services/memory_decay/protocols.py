"""Protocols for Ebbinghaus Memory Decay Engine (Rule 2)."""

from __future__ import annotations

import sys
from typing import Any, Protocol, runtime_checkable

from harness.services.memory_decay.models import (
    DecayConfig,
    EvictionDecision,
    MemoryNode,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


@runtime_checkable
class MemoryDecayService(Protocol):
    """Authoritative protocol for cognitive memory decay, reinforcement, and eviction."""

    def register_observation(
        self,
        node_id: str,
        content: str,
        *,
        category: str = "tool_output",
        current_turn: int = 0,
        initial_stability: float | None = None,
        metadata: dict[str, str] | None = None,
    ) -> MemoryNode:
        """Register a new observation or memory node into working memory."""
        ...

    def reinforce_recall(
        self,
        node_id: str,
        *,
        current_turn: int,
        alpha: float | None = None,
    ) -> MemoryNode | None:
        """Reinforce the stability of a memory node upon recall."""
        ...

    def calculate_retention(
        self,
        node_id: str,
        current_turn: int,
    ) -> float:
        """Calculate the current retention score R in [0.0, 1.0] for a node."""
        ...

    def evaluate_decay(
        self,
        current_turn: int,
        *,
        auto_evict: bool = True,
    ) -> EvictionDecision:
        """Evaluate retention across all stored nodes and evict sub-threshold items."""
        ...

    def get_node(self, node_id: str) -> MemoryNode | None:
        """Retrieve an immutable memory node by identifier."""
        ...

    def is_present(self, node_id: str) -> bool:
        """Check if a memory node is currently retained."""
        ...

    def working_set_size(self) -> int:
        """Return the count of active memory nodes."""
        ...

    def export_report(self) -> dict[str, Any]:
        """Export a serializable snapshot of memory metrics and retention states."""
        ...
