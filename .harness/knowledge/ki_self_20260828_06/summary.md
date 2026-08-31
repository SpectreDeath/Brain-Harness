# Subprocess Pipe Transport Lifecycle & Windows Proactor Guard

- **Knowledge Item ID**: `ki_self_20260828_06`
- **Category**: `sandboxing` / `process_isolation`
- **Isnad Status**: `VERIFIED`
- **Grounding**: `tests/test_deepened_creator.py`, `src/harness/plugins/sandbox.py`, `AGENTS.md` Rule 14

## Context & Problem Statement
When running asyncio subprocesses under the Windows Proactor event loop (`asyncio.create_subprocess_exec` / `create_subprocess_shell`), pipe handles for `stdin`, `stdout`, and `stderr` can be finalized in an unclosed state if the process terminates or raises an exception before explicit drainage. This results in Python `ResourceWarning: unclosed transport` or `PytestUnraisableExceptionWarning: I/O operation on closed pipe` during garbage collection.

## Invariant & Resolution Protocol
1. **Explicit Pipe Transport Closure**: In any `SubprocessExecutor` or sandbox execution wrapper, always wrap subprocess lifetime in `try...finally`.
2. **Drain and Close**:
   ```python
   try:
       stdout, stderr = await process.communicate(input=stdin_data)
   finally:
       for stream in (process.stdin, process.stdout, process.stderr):
           if stream and hasattr(stream, "close"):
               try:
                   stream.close()
               except Exception:
                   pass
   ```
3. **Process Wait**: Always await `process.wait()` before returning to ensure the underlying OS process handle is completely reaped.
