"""Internal utilities for CLI adapters and async command execution."""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any


def _run_async(coro: Any) -> Any:
    """Run an async coroutine from sync CLI context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)
