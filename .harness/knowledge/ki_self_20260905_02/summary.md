# PluginValidator Coroutine & Dual-Mode Invocation Invariant

**ID:** `ki_self_20260905_02`  
**Category:** `runtime_architecture`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `tests/test_youtube_transcript_fetcher.py#L303`, `src/harness/creator/validator.py`, `commit#fb9ffb6`, `AGENTS.md#Rule38`

## Executive Summary
In `src/harness/creator/validator.py`, `PluginValidator.validate()` is defined as an asynchronous coroutine (`async def validate()`) because sandbox dry-run execution requires async subprocess execution. Synchronous test harnesses or CLI commands that invoke `validator.validate(...)` without `await` receive an unawaited coroutine object, immediately raising `AttributeError: 'coroutine' object has no attribute 'valid'` when evaluating the validation report.

## Architectural Invariants & Rules
1. **Synchronous Invocation Bridge**: Synchronous callers must invoke `PluginValidator.validate_sync(...)`, which safely drives the async event loop using `asyncio.run()`.
2. **Async Test Decoration**: In pytest test suites, tests verifying plugin validation must be marked with `@pytest.mark.asyncio` and invoke `await validator.validate(...)`.
3. **Slotted Dataclass Contract**: The report returned by both synchronous and asynchronous invocations is a slotted `ValidationReport` with `.valid: bool` and `.checks: list[ValidationCheck]`.
4. **Codification**: Formally codified as `AGENTS.md` Rule 38.
