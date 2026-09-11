# Context File Linter & CI Integration Guide

## Why Context Files Rot

Context files rot for the same reason documentation rots: **nothing breaks when they are wrong**.
- A developer renames `src/services/task.js` to `src/services/tasks.js`. The context file still points to the old path.
- A script `typecheck` is deleted from `package.json`. The agent repeatedly attempts to run it, wasting turns and failing.
- A teammate edits `CLAUDE.md` directly, causing `AGENTS.md` and `CLAUDE.md` to issue conflicting instructions.

The defense is to treat context files like production code: verify them with automated linters and fail the build on drift.

---

## The 4 Verification Checks

The bundled `context_linter.py` implements four independent checks:

1. **Token Ceilings**:
   - Compares the estimated token footprint of always-loaded files against maximum budgets.
   - Prevents incremental bloat from silently filling agent attention buffers.
2. **Prose Path Integrity**:
   - Strips code blocks to eliminate sample code snippets.
   - Scans prose backtick spans for path-like strings.
   - Asserts that every referenced file and directory actually exists on disk.
3. **Script Command Validity**:
   - Parses commands mentioned in backticks (`npm test`, `npm run build`).
   - Asserts that they correspond to declared scripts in `package.json` or project manifests.
4. **Generator Sync Drift**:
   - Checks that generated files (`CLAUDE.md`, `.github/copilot-instructions.md`) match the canonical output of `sync_context.py`.
   - Catches un-synced manual edits.

---

## CI & Pre-Commit Integration

### GitHub Actions (`.github/workflows/ci.yml`)

```yaml
name: CI Verification

on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Verify Context Files Integrity
        run: python .agents/skills/codebase-context-architect/scripts/context_linter.py --root .
```

### Pre-Commit Hook (`.husky/pre-commit` or `.git/hooks/pre-commit`)

```bash
#!/bin/sh
python .agents/skills/codebase-context-architect/scripts/context_linter.py --silent --root .
if [ $? -ne 0 ]; then
  echo "Error: Context files contain broken paths, dead scripts, or out-of-sync vendor files."
  echo "Run 'python .agents/skills/codebase-context-architect/scripts/sync_context.py' or fix references."
  exit 1
fi
```

### Claude Code Agent Hook (`.claude/settings.json`)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python .agents/skills/codebase-context-architect/scripts/context_linter.py --silent"
          }
        ]
      }
    ]
  }
}
```
