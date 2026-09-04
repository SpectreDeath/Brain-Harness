# Typed ServiceContext Container Guarantee over Duck-Typed Introspection

**ID:** `ki_self_20260904_scratch_03`  
**Category:** `kernel_architecture`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `scratch/audit_seams.py`, `scratch/generate_arch_brief.py`, `src/harness/agent/context_optimizer.py`, `AGENTS.md#Rule2`

## Executive Summary
A common architectural smell in extensible harnesses is defensive duck-typing across subsystem boundaries—checking `hasattr(self.context, "optional")`, `hasattr(self.context, "has")`, or `hasattr(self.context, "transaction")`. This occurs when class constructors permit `context: ServiceContext | None = None` without providing a concrete fallback. It weakens static type safety, masks missing dependencies during headless testing, and proliferates boilerplate.

## Architectural Invariants & Rules
1. **Default Container Initialization:** Subsystem coordinators and engines must initialize `self.context = context or ServiceContext()` during `__init__`.
2. **Typed Protocol Resolution:** Never use `hasattr(self.context, ...)`. Always invoke typed methods directly: `self.context.optional(KEY)`, `self.context.require(KEY)`, `self.context.has(KEY)`, or `self.context.transaction()`.
3. **Transaction Context Seam:** Encapsulate transactional tool executions inside `async with self.context.transaction():` rather than branching on ad-hoc duck-typing.
4. Codified in `AGENTS.md` Rule 2.
