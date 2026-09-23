# Subprocess Stderr Drainage, Ring Buffers, and Crash Visibility in Sandboxed Transports

## Problem
In asynchronous process architectures (e.g. JSON-RPC over subprocess pipes), creating a child process with `stderr=asyncio.subprocess.PIPE` without spawning an asynchronous consumer task leads to OS pipe buffer exhaustion (typically 4KB–64KB). When child plugins log diagnostic warnings or dump stack traces, the pipe buffer fills and the OS blocks the child process indefinitely, resulting in unexplained IPC timeouts. Furthermore, if a child crashes on startup before the first JSON-RPC handshake, checking process liveness alone yields opaque errors such as `TransportError: Process 'python' is not running`, completely concealing the underlying traceback.

## Solution
1. **Asynchronous Stderr Drain Loop**: In `StdioJsonRpcTransport`, spawn a dedicated background task (`_drain_stderr()`) immediately upon connection that reads `stderr` line-by-line until EOF.
2. **Bounded Ring Buffer**: Buffer incoming stderr lines inside a bounded ring buffer (`collections.deque(maxlen=50)`), preventing unbounded memory growth.
3. **Diagnostic Surfacing**: When a subprocess exits with non-zero status or a call times out, extract trailing lines from the buffer and append them directly to the `TransportError` or error payload.
4. **Staged Bridge Runners**: Execute sandboxed plugins via a dedicated staged script (`src/harness/plugins/bridge_runner.py`) that pre-configures UTF-8 standard stream codecs (`sys.stdin`, `sys.stdout`, `sys.stderr`) rather than relying on inline `python -c` strings.

## Operational Guideline
- Always drain `stderr` concurrently when spawning async subprocesses with piped standard streams.
- Never discard stderr when raising transport exceptions; include the last $N$ lines to facilitate zero-hop diagnosis of environment and import errors.
- Enforce `AGENTS.md` Rule 53 across all sandboxed plugin executors.

## Provenance
- Source files: `src/harness/plugins/transport.py`, `src/harness/plugins/bridge_runner.py`, `src/harness/plugins/sandbox.py`
- Verification suite: `tests/test_architecture_hardening.py`
- Repository Standard: `AGENTS.md` Rule 53
