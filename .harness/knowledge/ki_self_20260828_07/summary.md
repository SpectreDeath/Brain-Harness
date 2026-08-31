# Secure Credential Handling & Shell-Free Git Push Protocol

- **Knowledge Item ID**: `ki_self_20260828_07`
- **Category**: `devops` / `security`
- **Isnad Status**: `VERIFIED`
- **Grounding**: `terminal://powershell/subshell-expansion-error`, `AGENTS.md` Rule 15

## Context & Problem Statement
Executing authenticated CLI operations (such as `git push https://<token>@github.com/...`) using PowerShell or bash string variable interpolation (`$token`) inside automated subagent execution loops is error-prone:
1. Subshell runners often strip or fail to parse `$` environment variables in multi-command blocks.
2. Direct CLI string interpolation risks leaking credentials into process table arguments or terminal output logs.

## Invariant & Resolution Protocol
1. **Runner Script Isolation**: Read tokens directly inside an in-memory execution process (e.g. Python `subprocess.run`) rather than shell string concatenation.
   ```python
   import pathlib
   import subprocess

   tok = pathlib.Path(r"D:\GitHub\projects\Tokens\tokens.txt").read_text().strip()
   res = subprocess.run(
       ["git", "push", f"https://{tok}@github.com/SpectreDeath/Brain-Harness.git", "main"],
       capture_output=True,
       text=True,
   )
   tok = None  # Immediately zero in-memory reference
   ```
2. **Log Sanitization**: Never echo, log, or serialize the raw token in tracebacks or stdout.
