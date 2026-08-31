# KI-4: Async Initialization Task Reference Retention & Graceful Cancellation

## Overview & The Async Lifecycle Trap
When building async service drivers in Python (e.g. Neo4j, FalkorDB, Redis, or background workers), asynchronous initialization (index building, schema checks, health pings) is often kicked off in the background to avoid blocking constructor instantiation.

However:
1. If the reference returned by `asyncio.create_task()` is discarded, the Python runtime's garbage collector may collect the task mid-execution.
2. When the application or test suite shuts down, uncompleted background tasks produce noisy `Task was destroyed but it is still pending` warnings or unhandled cancellation exceptions.

## The Pattern in `Neo4jDriver` & `FalkorDriver`

From `graphiti_core/driver/neo4j_driver.py` and commit `abc00175`:
```python
class Neo4jDriver(GraphDriver):
    def __init__(self, ...):
        # 1. Store strong reference to background task
        self._init_task: asyncio.Task[None] | None = asyncio.create_task(
            self._ensure_indices_and_constraints()
        )

    async def close(self) -> None:
        # 2. Cancel and await background task gracefully
        if self._init_task is not None and not self._init_task.done():
            self._init_task.cancel()
            try:
                await self._init_task
            except asyncio.CancelledError:
                pass
            self._init_task = None

        # 3. Close the underlying driver/connection pool
        if self._driver is not None:
            await self._driver.close()
```

## Application to Brain Harness
- Apply this pattern across all Brain Harness plugin lifecycles, background event dispatchers, and async I/O drivers to guarantee zero-leak test runs and clean teardowns.
