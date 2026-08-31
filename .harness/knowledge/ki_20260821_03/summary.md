# PowerShell String Parsing Pitfall Guard

## Problem
Python scripts generating shell commands for `run_command` use `strip('\"\\'')` to clean quoted strings. This works in bash/cmd but fails in PowerShell with `Unexpected token` errors because PowerShell parses quotes differently.

## Solution
Use explicit quote-type alternation instead of generic strip:
- If the outer shell is PowerShell, prefer single-quoted Python strings or escaped double quotes.
- Never pass `strip('\"\\'')` across shell boundaries without testing on the target shell.

## Operational Guideline
When a `run_command` step returns `Unexpected token` at a `strip(...)` call site, switch to shell-aware string construction. For PowerShell targets, use raw strings with explicit quote characters rather than regex-based stripping.

## Provenance
- Source brain: `antigravity_core`
- Primary source: `297ade4b-bce0-4653-a64a-20cbc7d11b3e.system_generated/logs/transcript.jsonl#L51`
- Distilled from: Multiple PowerShell parsing failures in skill scaffolding scripts