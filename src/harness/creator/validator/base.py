"""Base abstractions and synchronous event loop bridge for validation rules."""

from __future__ import annotations

from abc import ABC, abstractmethod

from harness.creator.validator.models import ValidationContext
from harness.services.storage.async_bridge import _run_coro_sync


class ValidationRule(ABC):
    """Abstract validation check rule."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the validation check rule."""

    @property
    def category(self) -> str:
        """Category domain of the rule."""
        return "structural"

    @abstractmethod
    async def validate(self, ctx: ValidationContext) -> bool:
        """Execute validation rule. Returns True if pipeline can continue, False if fatal."""


__all__ = ["ValidationRule", "_run_coro_sync"]
