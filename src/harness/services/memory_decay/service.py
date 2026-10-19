"""Default Ebbinghaus Memory Decay Engine implementation."""

from __future__ import annotations

import math
import sys
import time
from typing import Any

from harness.services.memory_decay.models import (
    DecayConfig,
    EvictionDecision,
    MemoryNode,
)
from harness.services.memory_decay.protocols import MemoryDecayService

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class DefaultMemoryDecayService(MemoryDecayService):
    """In-memory cognitive retention engine with non-linear recall reinforcement."""

    def __init__(self, config: DecayConfig | None = None) -> None:
        self.config = config or DecayConfig()
        self._store: dict[str, MemoryNode] = {}
        self._eviction_history: dict[str, int] = {}

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
        stability = (
            initial_stability
            if initial_stability is not None and initial_stability > 0.0
            else float(self.config.half_life_turns)
        )
        meta_tuples: tuple[tuple[str, str], ...] = ()
        if metadata:
            meta_tuples = tuple(sorted(metadata.items()))

        node = MemoryNode(
            node_id=node_id,
            content=content,
            category=category,
            stability=stability,
            recall_count=1,
            created_turn=current_turn,
            last_accessed_turn=current_turn,
            metadata=meta_tuples,
        )
        self._store[node_id] = node
        return node

    def reinforce_recall(
        self,
        node_id: str,
        *,
        current_turn: int,
        alpha: float | None = None,
    ) -> MemoryNode | None:
        existing = self._store.get(node_id)
        if existing is None:
            return None

        eff_alpha = alpha if alpha is not None else self.config.stability_boost_alpha
        new_recall_count = existing.recall_count + 1

        if self.config.reinforcement_mode == "logarithmic":
            growth_factor = 1.0 + eff_alpha * math.log(1.0 + new_recall_count)
        else:
            growth_factor = 1.0 + eff_alpha

        new_stability = existing.stability * growth_factor
        updated = MemoryNode(
            node_id=existing.node_id,
            content=existing.content,
            category=existing.category,
            stability=new_stability,
            recall_count=new_recall_count,
            created_turn=existing.created_turn,
            last_accessed_turn=max(existing.last_accessed_turn, current_turn),
            metadata=existing.metadata,
        )
        self._store[node_id] = updated
        return updated

    def calculate_retention(self, node_id: str, current_turn: int) -> float:
        node = self._store.get(node_id)
        if node is None:
            return 0.0
        elapsed = current_turn - node.last_accessed_turn
        if elapsed <= 0:
            return 1.0
        return math.exp(-float(elapsed) / node.stability)

    def evaluate_decay(
        self,
        current_turn: int,
        *,
        auto_evict: bool = True,
    ) -> EvictionDecision:
        t0 = time.perf_counter()
        evicted: list[str] = []
        retained: list[str] = []
        scores: list[tuple[str, float]] = []

        for node_id, node in list(self._store.items()):
            r = self.calculate_retention(node_id, current_turn)
            scores.append((node_id, r))
            if r < self.config.retention_threshold:
                evicted.append(node_id)
                if auto_evict:
                    self._eviction_history[node_id] = current_turn
                    del self._store[node_id]
            else:
                retained.append(node_id)

        # Enforce max_nodes bound if auto_evict is enabled
        if auto_evict and len(self._store) > self.config.max_nodes:
            surplus = len(self._store) - self.config.max_nodes
            retained_scores = [(nid, self.calculate_retention(nid, current_turn)) for nid in retained]
            retained_scores.sort(key=lambda x: x[1])
            for i in range(surplus):
                lowest_id = retained_scores[i][0]
                if lowest_id in self._store:
                    evicted.append(lowest_id)
                    if lowest_id in retained:
                        retained.remove(lowest_id)
                    self._eviction_history[lowest_id] = current_turn
                    del self._store[lowest_id]

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return EvictionDecision(
            evicted_ids=tuple(evicted),
            retained_ids=tuple(retained),
            retention_scores=tuple(scores),
            elapsed_ms=elapsed_ms,
        )

    def get_node(self, node_id: str) -> MemoryNode | None:
        return self._store.get(node_id)

    def is_present(self, node_id: str) -> bool:
        return node_id in self._store

    def working_set_size(self) -> int:
        return len(self._store)

    def export_report(self) -> dict[str, Any]:
        return {
            "active_nodes": len(self._store),
            "evicted_total": len(self._eviction_history),
            "half_life_turns": self.config.half_life_turns,
            "retention_threshold": self.config.retention_threshold,
            "reinforcement_mode": self.config.reinforcement_mode,
        }
