"""Base abstractions and synchronous event loop bridge for validation rules."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any

from harness.creator.validator.models import ValidationContext


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


def _run_coro_sync(coro: Any) -> Any:
    """Safely run a coroutine synchronously even within existing event loops."""
    async def _wrapped() -> Any:
        try:
            return await coro
        finally:
            await asyncio.sleep(0.01)

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, _wrapped()).result()
    return asyncio.run(_wrapped())
