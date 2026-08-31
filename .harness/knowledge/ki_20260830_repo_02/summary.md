# Invariant Verification Gates

## Context
Standard linters and type checkers are not always capable of verifying complex project-specific constraints, such as ensuring documentation references match code, package configuration invariants are upheld, or specific architectural boundaries are respected across module borders.

## Distilled Learning
Implement dedicated verification scripts (e.g., `verify-package-invariants.ts`, `verify-doc-site-fragments.ts`) that execute as explicit gates in the CI pipeline. This ensures project-specific rules are enforced without forcing developers to write complex custom linter plugins.

## Triggers & Seam Choices
- **Trigger**: When architectural rules, documentation links, or repository constraints are repeatedly broken due to a lack of automated enforcement.
- **Seam Choice**: Co-locate verification scripts in a `scripts/` directory and run them as part of the `check` or `test` phase in CI (e.g., `npm run check:ci:invariants`).
