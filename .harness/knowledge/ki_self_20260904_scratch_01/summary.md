# Headless Git Authentication, Credential Helper Exclamation Invariant & In-Memory Redaction

**ID:** `ki_self_20260904_scratch_01`  
**Category:** `security_and_forensics`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `scratch/git_push_with_token.py`, `scratch/git_push_noninteractive.py`, `AGENTS.md#Rule15`

## Executive Summary
In headless CI, worker proactors, or autonomous subagent environments, interactive Git Credential Manager (GCM) browser prompts fail with exit code 128 (`terminal prompts disabled`). Attempting to configure custom command helpers via `git -c credential.helper="python helper.py"` fails because Git syntax mandates a leading exclamation mark `!` (`!python <path>`) for external shell commands; omitting `!` causes Git to search for a builtin executable named `git-credential-<val>`.

## Architectural Invariants & Rules
1. **Exclamation Mark Prefix for Custom Helpers:** Always specify custom credential helper commands in Git configuration with a leading exclamation mark: `git -c credential.helper="!"python" "<helper_path>""`.
2. **Persistent Ingestion via Pipe:** To populate Git Credential Manager without interactive GUI prompts, pipe standard key-value tuples into `git credential approve` (`protocol=https\nhost=github.com\nusername=...\npassword=...\n\n`).
3. **Isolated Authenticated URL Pushing:** For immediate headless authenticated pushes, pass the authenticated URL directly as an element in Python `subprocess.run(["git", "push", auth_url, branch])` argv list (never evaluated via shell string interpolation).
4. **In-Memory Stream Redaction:** Always sanitize stdout and stderr streams in-memory before printing or logging (`clean_output = output.replace(token, "***TOKEN***")`).
5. Codified in `AGENTS.md` Rule 15.
