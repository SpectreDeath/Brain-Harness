# AST-Grep Structural Pattern Enforcement over Generic Linters

## Context
Standard linters (ESLint, flake8) excel at stylistic hygiene and simple AST node checks, but become prohibitively slow or complex when enforcing deep structural architectural rules—such as prohibiting certain method calls in specific subpackages, ensuring proper yield syntax in generators, or preventing bypass of concurrency wrappers.

## Distilled Learning
Adopt a two-tier structural verification pipeline:
1. **High-Speed Tier 1 Syntactic Pass**: Use Rust-powered syntax linters (`oxlint`, `ruff`) for sub-second formatting and basic diagnostics.
2. **Structural Architectural Pass with `ast-grep`**: Define declarative YAML rules (`script/ast-grep/sgconfig.yml`) that search for complex structural patterns, e.g.:
   - Detecting manual Promise instantiations where Effect constructors must be used.
   - Forbidding imports from private internal modules across package boundaries.
   - Auto-verifying simplification rules with `ast-grep test`.

## Triggers & Seam Choices
- **Trigger**: Architectural guardrails that need to be enforced across thousands of files without degrading developer inner-loop velocity.
- **Seam Choice**: Integrate AST-grep rule suites into `git pre-commit` hooks and CI pipelines alongside fast linters.
