# Win32 Job Object Kernel Memory Boundaries, CPython Baseline Footprint, and Subprocess Termination Triangulation

## Problem
In sandboxed subprocess execution on Windows, user-space memory watchdogs rely on polling process RSS (`psutil` or `ctypes.GetProcessMemoryInfo`) on a fixed interval (e.g. 50ms–2000ms). This periodic polling introduces CPU overhead and permits memory spikes to allocate substantial physical memory before the watchdog can terminate the process.

To achieve instant OOM enforcement, native Win32 Job Objects (`CreateJobObjectW`, `SetInformationJobObject` with `JOBOBJECT_EXTENDED_LIMIT_INFORMATION` and `JOB_OBJECT_LIMIT_PROCESS_MEMORY`) can be attached to the child process. However, two critical edge cases arise:
1. **CPython Bootstrap Allocation Floor**: A standard CPython interpreter allocates ~15MB–20MB of memory during initialization before loading any user script. Clamping a Job Object memory limit below this threshold causes an immediate C runtime crash (`Fatal Python error: init_import_site: Failed to import the site module / ImportError: Frozen object named 'site' is invalid`).
2. **Silent Unhandled Process Death**: When the Windows kernel terminates a process for exceeding a Job Object limit, the process exits instantly. A user-space watchdog loop never wakes up to observe high RSS, leaving `self._memory_exceeded = False`. Consequently, subsequent calls to `execute()` see `not self.is_running` and return an unhandled status dictionary `{"status": "error", "error": "Subprocess not running"}` instead of raising `SandboxError`.

## Solution
1. **Runtime Allocation Floor**: Enforce a minimum practical Job Object limit ceiling ($\ge 32	ext{ MB}$) for Python sandboxes on Windows to guarantee clean interpreter initialization.
2. **Termination Triangulation**: In `SubprocessExecutor.execute()`, check whether `self._win32_job_handle` is active when `not self.is_running`. If the process terminated while assigned to an active memory-constrained Job Object, synchronously raise `SandboxError("subprocess", f"Process exceeded memory limit of {self._memory_limit_mb:.0f} MB")`.
3. **Dual Enforcement Strategy**: Maintain the background software watchdog for cross-platform portability while using Job Objects on Windows as the authoritative hardware-level circuit breaker.

## Operational Guideline
- Never configure a Python subprocess memory limit below 32MB on Windows when using Job Objects.
- Always check Job Object handles and process exit codes to distinguish memory termination from graceful shutdown.
- Verify memory limits against `test_subprocess_memory_watchdog` in `tests/test_architectural_modernization.py`.

## Provenance
- Source files: `src/harness/plugins/sandbox.py`, `src/harness/plugins/transport.py`
- Verification suite: `tests/test_architectural_modernization.py:test_subprocess_memory_watchdog`
- Commits: `c04d401`, `52a308f`
