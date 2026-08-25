"""Thread-Safe Async/Sync Execution Seam for Tool Handlers.

Prevents `RuntimeError: This event loop is already running` when synchronous tool
functions are invoked inside active asyncio event loops or agent runtimes.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")

# Shared thread pool executor for running async tasks from within an active loop
_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=8, thread_name_prefix="gev_worker_")


def run_sync_safe(coro: Coroutine[Any, Any, T]) -> T:
    """Execute a coroutine synchronously without crashing if an event loop is already active."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is None:
        # No loop running in current thread, standard asyncio.run is safe
        return asyncio.run(coro)

    # Loop is active in current thread: delegate to worker thread to avoid nested loop conflict
    def _run_in_new_loop() -> T:
        new_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()

    future = _EXECUTOR.submit(_run_in_new_loop)
    return future.result()
