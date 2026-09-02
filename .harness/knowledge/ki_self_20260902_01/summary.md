# PowerShell Multi-Line Python String Escaping & Scratch File Execution

**ID:** `ki_self_20260902_01`  
**Category:** `execution_and_runtime`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `transcript.jsonl#task-15`, `AGENTS.md#Rule29`

## Executive Summary
Never execute multi-line Python logic via inline `python -c "..."` in PowerShell; always author to a dedicated scratch file (`<artifact_dir>/scratch/<name>.py`) and execute with `python <path>`. Inline `-c` strings repeatedly break on PowerShell quotation escapes, f-string braces, and nested string literals.

## Architectural Invariants & Rules
1. All multi-line Python automation scripts must be written to disk as scratch files.
2. PowerShell command invocations must execute the file path (`python <path>`) rather than inline code strings.
3. Scratch scripts must explicitly reconfigure standard output streams to UTF-8 (`sys.stdout.reconfigure(encoding='utf-8')`).
