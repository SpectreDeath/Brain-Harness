# Knowledge Item: Inspect-Before-Edit Seam QA & Adversarial Diff Verification

- **ID**: `ki_self_20260828_03`
- **Category**: `testing` / `quality_assurance`
- **Status**: `VERIFIED`

## Summary & Heuristic

Autonomous coding agents often fail by guessing implementation details and immediately modifying target files, creating silent syntax errors and broken imports.

### Core Guidelines:
1. **Inspect-Before-Edit Protocol**: Read the target file, its tests, and its importing callers before proposing or executing changes.
2. **DAG Component Seam Mapping**: Identify Michael Feathers seams (object boundaries, link seams, compile seams) and map the dependency DAG.
3. **Test-Driven Contracts**: Author or update a test that asserts the desired behavior before making production code modifications. Run `pytest` to confirm red-to-green state transitions.
4. **Minimal Diff Edits**: Produce tightly focused changes rather than rewriting entire files.
5. **Adversarial Diff Audits**: Demand a complete `git diff` review graded on an adversarial 1–10 severity scale to detect edge-case regressions, unhandled exceptions, and dead code before committing.
