"""Token budgeting and governance for multi-agent swarm execution."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


class TokenGovernor:
    """Tracks and bounds cumulative token consumption across swarm agents."""

    def __init__(self, max_tokens: int = 100_000) -> None:
        self.max_tokens = max_tokens
        self.tokens_consumed = 0
        self._usage_by_agent: dict[str, int] = defaultdict(int)

    @property
    def remaining_budget(self) -> int:
        return max(0, self.max_tokens - self.tokens_consumed)

    def allocate(self, agent_id: str, requested: int) -> int:
        """Grant token allocation up to available remaining global budget."""
        granted = min(requested, self.remaining_budget)
        return granted

    def record_usage(self, agent_id: str, tokens: int) -> None:
        """Record actual tokens consumed by an agent."""
        self.tokens_consumed += tokens
        self._usage_by_agent[agent_id] += tokens

    def is_exhausted(self) -> bool:
        """Check if global budget is completely exhausted."""
        return self.tokens_consumed >= self.max_tokens

    def get_stats(self) -> dict[str, Any]:
        return {
            "max_tokens": self.max_tokens,
            "tokens_consumed": self.tokens_consumed,
            "remaining_budget": self.remaining_budget,
            "usage_by_agent": dict(self._usage_by_agent),
            "is_exhausted": self.is_exhausted(),
        }


__all__ = ["TokenGovernor"]
