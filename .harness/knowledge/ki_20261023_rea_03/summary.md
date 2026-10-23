# Bounded Worker Control Framing and NUL-Delimited IPC Streams

## Core Architectural Principle

When orchestrating external reverse engineering engines or persistent interactive debuggers (Rizin, GDB, Frida, Ghidra), standard line-based `\n` buffers risk deadlock due to ANSI escape sequences, raw binary payload fragments, or unbuffered standard error output.

## Operational Pattern

1. **NUL-Delimited or Length-Prefixed Framing:**
   - Use explicit `\0` (NUL) framing bytes or 4-byte length prefixes for all command/response payloads across IPC pipes.
   - Enforce an upper bound on line length (e.g. 64 KB) to immediately detect and reject runaway output before pipe buffers saturate.

2. **Dedicated Stderr Drainage (Rule 53):**
   - Standard error streams must never share blocking locks with standard output.
   - Subprocess supervisors must spawn a non-blocking asynchronous drain task consuming `stderr` into a bounded ring buffer (`deque(maxlen=50)`).
   - On subprocess error or timeout, trailing lines are extracted from the ring buffer for immediate diagnostic surfacing.

## Provenance
- **Source Repository:** `morluto/rea`
- **Source Module:** `src/process/BoundedControlLines.ts` (L1-L85)
- **Commit:** `34563fcc9`
