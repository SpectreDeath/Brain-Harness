"""Synchronous event loop bridge utility for service-layer async operations."""

from __future__ import annotations

import asyncio
from typing import Any


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


__all__ = ["_run_coro_sync"]
