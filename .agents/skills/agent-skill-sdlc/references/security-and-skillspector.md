# SkillSpector Security Auditing & Pre-Flight Risk Matrix

## Overview: The Security Threat Model of Agent Skills

Agent skills run inside client environments with access to local filesystems, environment variables, git repositories, and shell execution runners. Ingesting untrusted third-party skills exposes systems to:
- **Arbitrary Code Execution**: Bundled scripts invoking `eval()`, `exec()`, or unvalidated `subprocess.run()`.
- **Credential Exfiltration**: Scanning `.env` or `~/.ssh` and transmitting tokens to remote endpoints.
- **Supply Chain Poisoning**: Untracked, unpinned dependencies in scripts.
- **Process Blocking**: Interactive scripts calling `input()`, freezing headless proactor transports.

---

## The 70-Pattern SkillSpector Audit Framework

The **SkillSpector** framework categorizes AST code patterns, frontmatter grants, and prompt instructions into four weighted risk dimensions:

1. **Dangerous System Calls (Weight: 30%)**:
   - `eval()`, `exec()`, `__import__()`, `ctypes`, `os.system()`
2. **Network & Exfiltration Vectors (Weight: 30%)**:
   - Outbound HTTP sockets (`socket.connect`, `requests.post` to unvetted domains), webhook dispatches
3. **Filesystem & State Mutation (Weight: 20%)**:
   - Destructive operations (`shutil.rmtree`, `git reset --hard`, unbounded write loops)
4. **Environment & Credential Access (Weight: 20%)**:
   - Reading `os.environ["API_KEY"]`, `.aws/credentials`, `.ssh/id_rsa`

---

## Risk Score Calibration & Action Bands

Every audited skill is assigned an aggregate **Security Risk Score** ($0 - 100$):

```
┌─────────────────────────────────────────────────────────────┐
│                 SKILLSPECTOR RISK BANDS                     │
├───────────────┬──────────────┬──────────────────────────────┤
│ Score Range   │ Risk Band    │ Policy Enforcement Action    │
├───────────────┼──────────────┼──────────────────────────────┤
│ 0 – 20        │ SAFE         │ Automatic Approval & Register│
│ 21 – 50       │ CAUTION      │ Manual Approval Seam Required│
│ 51 – 80       │ HIGH         │ Prohibited in Production     │
│ 81 – 100      │ CRITICAL     │ Immediate Quarantine & Block │
└───────────────┴──────────────┴──────────────────────────────┘
```

### Band Descriptions:

- **SAFE (0–20)**:
  - Read-only operations, pure AST parsing, deterministic file generation.
  - Relocatable paths; zero external network dependencies.
  - Passes directly into `.agents/skills/`.

- **CAUTION (21–50)**:
  - Local file modification, git branch staging, or bounded package installation via `uv`.
  - Requires explicit human operator review before installation.

- **HIGH (51–80)**:
  - Dynamic subprocess execution, shell scripting without parameter escaping, unpinned dependencies.
  - Prohibited from unattended production execution; requires sandbox isolation.

- **CRITICAL (81–100)**:
  - Unobfuscated network socket dials, credential reads, destructive root file operations.
  - Blocked by CI linter; immediately logged to security telemetry.

---

## The Pre-Flight Security Checklist

Before committing or releasing an agent skill, verify all items on the checklist:

- [ ] **No Interactive Calls**: Zero occurrences of `input()` or interactive prompts in bundled scripts.
- [ ] **Path Relocatability**: All paths resolved via `Path(__file__).resolve().parent` or CLI flags; no hardcoded absolute user directories.
- [ ] **Least Privilege Frontmatter**: `allowed-tools` explicitly restricted to necessary capabilities.
- [ ] **UTF-8 Codec Enforcement**: All scripts explicitly configure standard streams to UTF-8 (`sys.stdout.reconfigure(encoding="utf-8")`).
- [ ] **Deterministic Cleanups**: All temporary files written to `%TEMP%` or scratch directories with explicit cleanup handlers.
- [ ] **Pinned Dependencies**: Bundled scripts declare PEP 723 metadata blocks with exact package version bounds.

---

## CI/CD Gate Integration Example

Add a validation and audit step to your repository CI pipeline:

```yaml
name: Agent Skill Pre-Flight Audit

on: [push, pull_request]

jobs:
  audit-skills:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Validate Skills
        run: |
          for skill_dir in .agents/skills/*/; do
            python $skill_dir/scripts/validate_skill.py "$skill_dir" --json || exit 1
          done
```
