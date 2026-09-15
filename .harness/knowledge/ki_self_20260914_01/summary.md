# Skill-to-IoC Micro-Kernel Seam Elevation Lifecycle

## Executive Summary
This Knowledge Item documents the foundational architectural pattern for elevating standalone CLI skills into authoritative in-memory micro-kernel services, governed by **Rule 49** (*Skill-to-IoC Micro-Kernel Seam Elevation Invariant*).

## Architectural Mechanics
1. **The CLI Sprawl Friction**: Standalone skills in `.agents/skills/<name>/` start as filesystem scripts executed via `subprocess.run(["python", ...])`. In multi-turn agent loops or swarm deliberation, out-of-process subprocess forks introduce 150ms+ startup latency, stdin/stdout serialization overhead, and lack transactional rollback boundaries.
2. **IoC Protocol Seam**:
   - Define a slotted, typed `@runtime_checkable` domain protocol and `ServiceKey[T]` in `src/harness/services/<name>.py`.
   - Export domain request/response models via typed Pydantic structures.
   - Re-export the protocol and key in `src/harness/services/__init__.py`.
3. **Domain-Partitioned Plugin Registration**:
   - Implement an isolated plugin in `plugins/<category>/<name>/main.py` subclassing `HarnessPlugin`.
   - In `on_load(context)`, provide the service instance via `context.provide(KEY, instance)`.
   - Explicitly export the instantiated module-level singleton `plugin = MyPlugin()` (Rule 45).
4. **Thin CLI Dispatcher**:
   - Refactor `scripts/<cli>.py` into a thin argument parser that imports the slotted domain engine directly, maintaining CLI utility for human operators while eliminating redundant subshells.

## Verifiable Isnad Lineage
- **Grounding Trajectories**: `ca677d26` (Rule 49 inception and deepening loop), `2664f7a5` (pr-lens triad forge codification), `f93c8b01` (DeepSelect TopK forge).
- **Governing Invariants**: `AGENTS.md` Rule 1, Rule 2, Rule 18, Rule 45, Rule 49.
