# Shim: 4-Tier Capability Permission Gating & Symlink Sandbox

## Overview
- **Source Repository**: `https://github.com/Balanov/shim` (`3b5acfdf`)
- **Primary Files**:
  - `internal/tools/tools.go#L18-L134`
  - `internal/tools/files.go#L40-L128`
  - `internal/tools/shell.go#L44-L100`

## Core Architecture & Invariants
1. **Four Tool Capability Levels (`Level`)**: Every tool explicitly declares `read`, `write`, `shell`, or `external`. Mutating and side-effecting surfaces are never unlabeled.
2. **Three Permission Enforcement Modes (`Executor.Execute`)**:
   - `read-only`: Hard-rejects any tool whose capability level is not `read`.
   - `ask`: Allows `read` tools silently and requires explicit interactive confirmation (`y`/`yes`) for `write`, `shell`, or `external` invocations.
   - `auto`: Permits execution without confirmation prompts.
3. **Closed Tool Parameter Schemas (`Schema()`)**: Tool parameter objects always emit `"additionalProperties": false` so unexpected model arguments fail validation cleanly.
4. **Ancestor Symlink Containment (`FileTools.secure()`)**: Both the workspace root and every target path (falling back up parent directories until an existing ancestor resolves when creating new files) are evaluated with symlink resolution and verified via `filepath.Rel`-style containment (`within()`).
5. **Deterministic File & Shell Bounds**: `read()` rejects files over `2 MiB` (`2<<20`), NUL-byte binaries, and slices exceeding `2000` lines; shell execution defaults to a `120s` (`2 * time.Minute`) timeout and caps combined `Stdout`/`Stderr` at `1 MiB` (`1<<20`).

## Decision Heuristics & Anti-Patterns
- **Never resolve only `filepath.Abs` on file targets**: Non-existent leaf paths under symlinked parents bypass `Abs`; always walk to the deepest existing ancestor before containment checks.
- **Never allow unbounded file reads or shell buffers**: Enforce `2 MiB` / `2000` lines and `1 MiB` output ceilings before appending tool results to conversation state.
