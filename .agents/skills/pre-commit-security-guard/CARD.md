# Skill Summary Card: `pre-commit-security-guard`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:       pre-commit-security-guard                 │
│ Category:    security_and_forensics / shift-left       │
│ Invocation:  /pre-commit-security-guard                │
│ Trigger:     "pre-commit security", "shift security",  │
│              "setup devskim", "catch secrets git",     │
│              "gitleaks pre-commit", "local sast"       │
│ Version:     1.0.0                                     │
│ Provides:    "shift_left_security_guard"               │
├────────────────────────────────────────────────────────┤
│ Target:      Intercept vulnerabilities and secrets     │
│              before PRs using Git pre-commit hooks,    │
│              DevSkim SAST, Gitleaks, and CI defense.   │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Operational Sequence

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Toolchain & Labor** | Provision pre-commit, DevSkim CLI, and Gitleaks | Installed CLI toolchain | DevSkim & Gitleaks verified in PATH |
| **2. Hook Config & Dispatcher** | Scaffold multi-file loop and `.pre-commit-config.yaml` | `scripts/run-devskim.py` | Multi-file handling & hooks installed |
| **3. Failure Smoke Test** | Deliberate synthetic failure verification | Test failure fixtures | Both SAST and secrets reject commit (Exit 1) |
| **4. Triage & Baselines** | Run `--all-files` baseline, enforce inline suppressions | Clean suppression list | Zero blanket directory exclusions |
| **5. Dual-Gate CI Defense** | Mirror local checks in GitHub Actions with SARIF | `.github/workflows/security.yml` | Full history audit (`fetch-depth: 0`) & SARIF |

---

## The Three Pillars Cheat Sheet

### 1. Multi-File Dispatcher (`scripts/run-devskim.py`)
```python
import subprocess, sys

exit_code = 0
for filename in sys.argv[1:]:
    result = subprocess.run(["devskim", "analyze", "-I", filename])
    exit_code = exit_code or result.returncode
sys.exit(exit_code)
```

### 2. Pre-Commit Configuration (`.pre-commit-config.yaml`)
```yaml
repos:
  - repo: local
    hooks:
      - id: devskim
        name: DevSkim security lint
        entry: python scripts/run-devskim.py
        language: system
        types_or: [python, javascript, typescript, json, yaml]
        pass_filenames: true
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks
```

### 3. Dual-Gate CI Defense (`.github/workflows/security.yml`)
- `fetch-depth: 0` for complete commit history secret auditing.
- `upload-sarif` to publish DevSkim findings to GitHub Security tab.
- Neutralizes `--no-verify` local hook bypasses.

---

## Verification & Quality Checklist

- [ ] **Dual Scanner Division**: SAST linting (DevSkim) and secret scanning (Gitleaks) cleanly decoupled.
- [ ] **Multi-File Safe**: Python dispatcher iterates through staged files without breaking on single-arg CLI limits.
- [ ] **Synthetic Verification**: Both hooks verified to block commits on deliberate synthetic flaws before rollout.
- [ ] **Suppression Hygiene**: Inline comments used for justified false positives; zero blanket folder exclusions.
- [ ] **CI Parity**: Dual-gate CI workflow actively scans full commit history and surfaces SARIF alerts.
- [ ] **Single-Pipe Card Box**: Compliant with Rule 37 ASCII box standard (`│`).
