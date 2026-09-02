# PowerShell Argument Glob Non-Expansion & Keyword Filtering

**ID:** `ki_self_20260902_02`  
**Category:** `testing_and_verification`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `transcript.jsonl#task-102`, `AGENTS.md#Rule30`

## Executive Summary
PowerShell does not expand wildcard glob arguments (`*`) like Unix bash does, passing `tests/test_*.py` as a literal non-existent path string to pytest. All pytest suite runs targeting pattern subsets must use keyword expressions (`pytest -k "<pattern>"`) or pipe explicit file lists from PowerShell (`Get-ChildItem -Filter`).

## Architectural Invariants & Rules
1. Never pass bare wildcard glob patterns in pytest CLI command arguments on Windows.
2. Always use `pytest -k "<pattern>"` for pattern-based test selection.
3. For non-pytest CLI tools requiring globbed files, use explicit PowerShell `Get-ChildItem` pipelines.
