# Coarse OS Timer Resolution Bifurcation

> **Identifier:** `ki_self_20261109_03_coarse_os_timer_resolution_bifurcation`  
> **Category:** `testing`  
> **Author:** Brain Harness Reflector (`harness-reflector`)  
> **Status:** `ACTIVE` | **Isnād Status:** `VERIFIED`

---

## 1. Context & The Virtualization Timer Problem

Standard physical PCs provide high-resolution timers (`QueryPerformanceCounter`), but virtualized hypervisors (such as GitHub Actions `windows-latest` VM runners) default to standard Windows interrupt timer ticks of $15.625	ext{ ms}$ ($64	ext{ Hz}$).

When authoring unit tests for timeout mechanics:
1. Setting tight wall-clock deadlines (e.g. `timeout_seconds = 0.05`) means the deadline expires within only 3 timer ticks.
2. If the hypervisor schedules CPU cycles unevenly or if a query executes in $0.048	ext{ s}$ on a fast Linux C-runtime, the query can complete *before* the timeout triggers, failing the assertion `assert "error" in response`.
3. Conversely, on a noisy VM, timer interrupts may be delayed by $30	ext{--}50	ext{ ms}$, causing non-deterministic test flakiness across CI matrix runs.

---

## 2. Invariant: The Bifurcated Testing Protocol

To achieve 100% deterministic test execution across Windows, Linux, and macOS without flakiness:
1. **Mock Monotonic Clocks for State Machine Boundaries**:
   - For fast unit tests verifying engine deadline checking and state transitions, use `unittest.mock.patch("time.monotonic")` with simulated time increments (`side_effect = [0.0, 10.0]`).
2. **Heavy Fixtures for Real Subprocess Wall-Clock Timeouts**:
   - To test real subprocess termination and IPC deadline enforcement across platforms, employ a fixture that is guaranteed to take substantially longer than the timeout deadline (e.g. a 1,500-node chain requiring ~1.2s on Linux and ~4.0s on Windows) paired with a moderate timeout (`timeout_seconds=0.2`) and an unbounded inference cap (`max_inferences=100_000_000`).

---

## 3. Empirical Verification & Isnād Lineage

- **Historical CI Failures**: Runs `#42517758361`, `#42518002144`, `#42536112908`, `#42536369675`.
- **Bifurcated Tests**: `test_mcp_prolog_backend_timeout_mocked` and `test_mcp_prolog_backend_wall_clock_timeout`.
- **Result**: 11/11 CI jobs green across all operating systems in Run `#42536702405`.
