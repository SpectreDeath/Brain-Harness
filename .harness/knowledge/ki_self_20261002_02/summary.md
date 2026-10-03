# Shared Memory (SHM) IPC Acceleration & Safe Native Engine Graceful Degradation

## Problem
In sandboxed execution environments:
1. When transferring large payload objects (>64KB, such as whole-repository AST repo maps, large test transcripts, or visual briefs) across standard input/output pipes, JSON encoding and byte stream piping degrade latency and can fill proactor OS pipe buffers (causing deadlocks).
2. Introducing WebAssembly engines (e.g. Wasmtime WASI runtime) for leaf data transformations risks catastrophic plugin failure on environments where native C-extension wheels (`wasmtime`) cannot be installed or compiled (`ModuleNotFoundError: No module named 'wasmtime'`).

## Solution
1. **Shared Memory Handshake & Capability Negotiation**:
   - `StdioJsonRpcTransport` negotiates capability flags (`shm_available`) during handshake.
   - For payloads over threshold (64KB), a `multiprocessing.shared_memory.SharedMemory` block is mapped, passing only the block name across the pipe.
   - Handlers register defensive `atexit` hooks (`_cleanup_all_shm`) ensuring `.close()` and `.unlink()` are executed even on abnormal termination.
2. **Transparent Native-to-Subprocess Fallback**:
   - `WasmSandboxExecutor` inspects runtime availability. If `wasmtime` is missing or fails to initialize, the executor automatically delegates execution to the battle-tested `SubprocessExecutor` sandbox without raising fatal errors to callers.

## Operational Guideline
- Never assume POSIX shared memory handles automatically unlink on Windows; explicitly guard `.unlink()` calls on non-Windows platforms.
- Threshold payload sizes ($\ge 64\text{ KB}$) before activating SHM to avoid memory setup overhead on tiny RPC messages.
- Always provide fallback to subprocess sandboxes when integrating native virtualization layers.

## Provenance
- Source files: `src/harness/plugins/transport.py`, `src/harness/plugins/bridge_runner.py`, `src/harness/plugins/sandbox.py`
- Test contracts: `tests/test_sandbox.py::test_transport_capability_negotiation`, `test_transport_shm_round_trip`, `tests/test_wasm_sandbox.py`
- Empirical trace: Transcript `ed7c4cf2-8671-4f6b-ad48-a7a0e1aa8a17` Step 353
