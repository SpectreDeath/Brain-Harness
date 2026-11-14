# Micro-Kernel Composition Root & Rule 45 Plugin Singletons

## Finding (Deep Audit Axis 1 & Axis 3)
- `mypy src/harness/kernel --ignore-missing-imports` surfaced 18 type errors across kernel files and transitive plugin imports.
- Five legacy plugins (`loop_engine`, `semantic_kernel_engine`, `wiki_compiler`, `context_compiler`, `vibe_scanner`) lacked a `HarnessPlugin` subclass and module-level `plugin` singleton.

## Remediation
- Resolved all 18 type errors across kernel and transitive plugin files (`37` kernel source files clean).
- Documented the Composition Root Boundary invariant in `src/harness/kernel/README.md`.
- Exported `HarnessPlugin` subclasses and `plugin = ...` singletons in all five legacy plugins.
