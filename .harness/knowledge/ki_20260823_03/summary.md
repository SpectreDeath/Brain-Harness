# Windows PowerShell Command Delimiter Normalization

## Problem
In cross-platform workflows, agents and automation pipelines frequently generate bash-style command strings:
```bash
python script_a.py && python script_b.py
```
On Windows PowerShell, this triggers an immediate syntax failure:
`ParserError: The token '&&' is not a valid statement separator in this version.`

## Solution
Normalize all shell command chains:
- **PowerShell Separator**: Use semicolon `;` instead of `&&`.
- **Conditional Chaining**: Use `if ($?) { ... }` or encapsulate sequential logic inside a single Python script.
- **Temporary Directories**: Use standard Python `tempfile.gettempdir()` or `%TEMP%` instead of hardcoded `/tmp`.

## Operational Guideline
- Disallow unescaped `&&` tokens in any Windows command runner invocations.
- Encapsulate multi-step pipelines into self-contained Python scripts whenever possible.

## Provenance
- CLI Runner: [`src/harness/cli.py:L870-948`](file:///d:/GitHub/projects/Brain%20Harness/src/harness/cli.py#L870-L948)
- Transcript Incident: [`transcript.jsonl#L29`](file:///d:/GitHub/projects/Brain%20Harness/.harness/mind-reader-results.json)
- Isnad Decision ID: `dec_20260823_03`
