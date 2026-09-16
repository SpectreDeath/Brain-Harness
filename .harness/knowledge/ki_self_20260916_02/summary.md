# ReAct Step Tool Safe-Loop Dispatch Invariant

## Executive Summary
This Knowledge Item defines the **ReAct Step Tool Safe-Loop Dispatch Invariant** (Rule 54), addressing event loop contention when ReAct step execution engines and async agent proactors invoke module-level synchronous tool wrappers.

## Architectural Mechanics
1. **The Event Loop Contention Hazard**:
   - In Python's `asyncio`, invoking `asyncio.run(coro)` from within a thread that already has an active running event loop (e.g. inside `StepExecutionEngine.run()`, a background worker proactor, or an interactive async test session) raises:
     ```python
     RuntimeError: asyncio.run() cannot be called from a running event loop
     ```
   - In Harness plugins, service protocols (`PaperlessNgxService`, `ChatbotXService`) are authored as non-blocking `async def` coroutines. However, tools exposed to ReAct agents (`entrypoints` in `plugin.json`) are often dispatched as synchronous functions (`def paperless_search_documents(...) -> dict[str, Any]`).
2. **The Safe-Loop Runner Pattern (`_safe_run`)**:
   - Every module-level synchronous tool wrapper must execute coroutines through an authoritative safe-loop helper:
     ```python
     def _safe_run(coro: Any) -> Any:
         try:
             loop = asyncio.get_running_loop()
         except RuntimeError:
             loop = None

         if loop and loop.is_running():
             with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                 return pool.submit(asyncio.run, coro).result()
         else:
             return asyncio.run(coro)
     ```
   - If no loop is active (e.g. simple CLI invocation), it falls back to standard `asyncio.run(coro)`.
   - If an event loop is active, it safely offloads execution to an isolated one-shot worker thread, blocking only that thread and returning the result without colliding with the caller's proactor event loop.
3. **Thread-Safe Dispatch Fidelity**:
   - This pattern ensures 100% interoperability between asynchronous micro-kernel services and synchronous tool-calling interfaces without requiring external dependencies like `nest_asyncio`.

## Verifiable Isnad Lineage
- **Grounding Implementations**:
  - `plugins/data_engineering/paperless_ngx/main.py:L32-L46` (`_safe_run`)
  - `tests/test_paperless_ngx_plugin.py:L250-L265` (`test_safe_run_in_active_event_loop`)
  - Commit `1b72bad`
- **Governing Rules**: `AGENTS.md` Rule 9 (Context Optimization), Rule 14 (Subprocess Pipe Transport), Rule 45 (Plugin Module Singleton), Rule 54 (Safe-Loop Invariant).
