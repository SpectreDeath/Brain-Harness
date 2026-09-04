# ValidationReport Interface Contract & Check Collection Invariant

**ID:** `ki_self_20260903_01`  
**Category:** `testing_and_verification`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `transcript.jsonl#step-145-150`, `src/harness/creator/validator.py`, `AGENTS.md#Rule34`

## Executive Summary
When verifying dynamically created or modified skills using `SkillValidator.validate()` or plugins using `PluginValidator.validate()`, callers must never assume the existence of a `.passed` or `.rules_passed` attribute on the returned `ValidationReport` instance. In `src/harness/creator/validator.py`, `ValidationReport` is a slotted dataclass exposing `.valid: bool` for the overall outcome and `.checks: list[ValidationCheck]` for individual test rule results. Attempting to query `report.passed` raises an immediate `AttributeError`.

## Architectural Invariants & Rules
1. Always evaluate overall validation success via `report.valid: bool`.
2. Inspect individual rule results via the `report.checks` collection, where each `ValidationCheck` instance contains `.rule: str`, `.passed: bool`, and `.message: str`.
3. Inspect errors and warnings directly through `report.errors: list[str]` and `report.warnings: list[str]`.
4. Codified in repository rule `AGENTS.md` Rule 34.
