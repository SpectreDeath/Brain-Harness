"""Error types for recursive harnessing."""

from __future__ import annotations


class ProposerError(RuntimeError):
    """A proposer session did not produce a usable reply. Never swallowed into an empty string."""

    def __init__(self, message: str, *, attempts: int = 0, cost_usd: float = 0.0) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.cost_usd = cost_usd


class SelectorError(RuntimeError):
    """The selector session did not yield a usable choice."""

    def __init__(self, message: str, *, cost_usd: float = 0.0) -> None:
        super().__init__(message)
        self.cost_usd = cost_usd
