### Distilled Heuristic
Agent tool invocations should execute inside context transactions ('async with context.transaction()') with automatic rollback ('await tx.dispose()') whenever the tool returns an error payload or raises an exception.

### Named Anti-Pattern
Mutating shared ServiceContext during tool execution without an ACID boundary.

### Empirical Evidence & Provenance
- **Sources**: harness-reflection-20260826-170011.html, harness-reflection-20260826-163347.html, harness-reflection-20260826-163323.html, harness-reflection-20260826-163040.html, architecture-review-20260826-harness-reflector.html, harness-reflection-20260826-145800.html, harness-reflection-20260826-074052.html, harness-reflection-20260826-074028.html, harness-reflection-20260826-073315.html, architecture-review-20260826.html
- **Confidence**: 96%
