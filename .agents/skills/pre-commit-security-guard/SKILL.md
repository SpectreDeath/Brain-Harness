---
name: pre-commit-security-guard
description: Shift security left by intercepting vulnerabilities and secrets before pull requests using Git pre-commit hooks, multi-file DevSkim SAST, Gitleaks, deliberate failure injection, and dual-gate CI enforcement. Do not use for dynamic penetration testing or cloud container runtime audits.
---

# Pre-Commit Security Guard: Shift-Left SAST & Secret Interception

The `pre-commit-security-guard` skill provides the definitive engineering framework for intercepting security vulnerabilities, insecure API usages, and exposed credentials on developer workstations before code ever reaches pull requests, CI runners, or production Git branches.

Synthesizing Umair Mirza's foundational methodology (*"How to Catch Security Vulnerabilities in Code Before They Reach Your Pull Requests"*, freeCodeCamp, 2026), this skill establishes a **dual-scanner defense**: pairing Microsoft CST's lightweight static application security testing (SAST) linter **DevSkim** with the dedicated high-entropy credential scanner **Gitleaks**, governed through Git pre-commit hooks, verified with deliberate failure smoke tests, and backed by mandatory CI SARIF reporting.

```
[1. Toolchain & Division of Labor] -> [2. Dispatcher & Hook Config] -> [3. Deliberate Failure Smoke] -> [4. Triage & Suppression] -> [5. Dual-Gate CI Defense]
```

See [CARD.md](CARD.md) for the companion quick-reference card, 5-stage matrix, and verification checklist.
Consult [crafting-skills](../crafting-skills/SKILL.md) for skill authoring standards and [epistemic-isnad-audit](../epistemic-isnad-audit/SKILL.md) for source provenance.

---

## 1. Multi-Engine Toolchain Provisioning & Division of Labor

A robust shift-left security architecture requires strict separation of concerns between code-pattern linting and credential entropy analysis.

1. **Enforce Scanner Division of Labor**:
   - **DevSkim CLI (Microsoft CST)**: Fast, developer-facing SAST linter. Inspects AST and lexical tokens for insecure cryptography (MD5, SHA1), dangerous API calls, insecure deserialization, command injections, and weak TLS configurations. DevSkim is *not* a secret scanner.
   - **Gitleaks**: Dedicated secret scanner. Uses regex patterns tuned for token shapes and Shannon entropy calculations to catch API keys, private tokens, passwords, and connection strings that slip past linters.
2. **Provision Local Toolchain**:
   - Install `pre-commit`:
     ```bash
     pip install pre-commit
     ```
   - Install DevSkim CLI as a .NET global tool or download the platform binary:
     ```bash
     dotnet tool install --global Microsoft.CST.DevSkim.CLI
     ```
   - Verify toolchain installation:
     ```bash
     pre-commit --version
     devskim --version
     ```

> **Completion criterion**: Pre-commit, DevSkim CLI, and Gitleaks available in path; division of labor between SAST linting and secret detection documented.

---

## 2. Pre-Commit Configuration & Multi-File Execution Dispatcher

DevSkim's CLI accepts a single target path via `-I`, whereas `pre-commit` appends all staged files as trailing command-line arguments. Passing multiple files directly breaks standard CLI invocation.

1. **Scaffold Python Multi-File Dispatcher (`scripts/run-devskim.py`)**:
   ```python
   import subprocess
   import sys

   exit_code = 0
   for filename in sys.argv[1:]:
       result = subprocess.run(["devskim", "analyze", "-I", filename])
       exit_code = exit_code or result.returncode

   sys.exit(exit_code)
   ```
2. **Configure `.pre-commit-config.yaml`**:
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
3. **Bind Git Hooks**:
   ```bash
   pre-commit install
   ```

> **Completion criterion**: Dispatcher script authored, `.pre-commit-config.yaml` declared with `pass_filenames: true`, and `.git/hooks/pre-commit` active.

---

## 3. Deliberate Synthetic Failure Verification

Never trust a security guardrail without verifying that it actively blocks commits.

1. **Smoke-Test SAST Hook (Insecure Cryptography)**:
   - Create a temporary fixture (`test_insecure.js` or `test_insecure.py`):
     ```javascript
     const crypto = require("crypto");
     const hash = crypto.createHash("md5").update("password").digest("hex");
     ```
   - Stage and attempt to commit:
     ```bash
     git add test_insecure.js
     git commit -m "test: verify devskim hook failure"
     ```
   - **Assert**: DevSkim rejects commit with non-zero exit code (Exit 1) and outputs rule diagnostic (`DS126858: Weak Hash Algorithm`).
2. **Smoke-Test Secret Scanner (Entropy / Key Detection)**:
   - Stage a shaped synthetic API key:
     ```javascript
     const apiKey = "4f2a9c1e7b6d3a8f0c5e9b2d7a41c6";
     ```
   - **Assert**: Gitleaks rejects commit with exit code 1, reporting leak detection.
3. **Post-Test Cleanup**:
   - Remove temporary test fixtures immediately. **Never use real credentials for testing.**

### The Visual Brief & Stakeholder Alignment

When onboarding repositories or aligning with engineering teams, generate an interactive visual brief in `%TEMP%\pre-commit-security-guard-<timestamp>.html` rendering the dual-scanner architecture DAG, failure smoke test matrices, and diagnostic scorecards using Mermaid.js and Tailwind CSS.

### Mandatory Checkpoint Gate

Before enabling blocking hooks on shared or production repositories, present an implementation plan with `RequestFeedback: true` confirming scanner parameters, legacy baseline results, and deliberate synthetic failure verification. **STOP and obtain stakeholder confirmation** before committing hooks to repository branches.

> **Completion criterion**: Both hooks independently confirmed to block commits with non-zero exit codes against synthetic failure fixtures; visual brief rendered in %TEMP% and mandatory checkpoint confirmed.

---

## 4. Progressive Triage, Suppression Hygiene & Legacy Baselines

Avoid paralyzing engineering velocity when rolling out hooks to legacy repositories.

1. **Establish Codebase Baseline**:
   - Run hooks manually against the entire repository once:
     ```bash
     pre-commit run --all-files
     ```
   - Catalog existing legacy violations without blocking day-to-day feature work.
2. **Enforce Surgical Inline Suppressions**:
   - When a finding is determined to be a benign or unexploitable false positive, suppress only that specific finding with an in-code comment and explicit rationale.
   - **Strict Negative Boundary**: Never apply blanket directory exclusions (e.g. `exclude: src/.*`). Broad directory exclusions create permanent blind spots.
3. **Preserve Sub-3s Hook Latency**:
   - Keep local pre-commit checks strictly focused on staged files (`pass_filenames: true`). Reserve full-repository audits for CI pipelines.

> **Completion criterion**: Legacy findings cataloged, inline suppressions documented with rationale, and zero blanket directory exclusions present.

---

## 5. Dual-Gate CI Defense & SARIF Security Governance

Local pre-commit hooks provide immediate developer feedback, but they can be bypassed with `git commit --no-verify`. Security enforcement must be duplicated in CI.

1. **Author GitHub Actions Workflow (`.github/workflows/security.yml`)**:
   ```yaml
   name: Security Checks

   on:
     pull_request:
     push:
       branches: [main]

   jobs:
     scan:
       runs-on: ubuntu-latest
       permissions:
         contents: read
         security-events: write
       steps:
         - uses: actions/checkout@v4
           with:
             fetch-depth: 0

         - uses: actions/setup-dotnet@v4
           with:
             dotnet-version: "8.0.x"

         - name: Install DevSkim
           run: dotnet tool install --global Microsoft.CST.DevSkim.CLI

         - name: Run DevSkim SARIF
           run: devskim analyze -I . -f sarif -O devskim.sarif

         - name: Upload DevSkim SARIF
           uses: github/codeql-action/upload-sarif@v3
           if: always()
           with:
             sarif_file: devskim.sarif

         - name: Run Gitleaks Full History Audit
           uses: gitleaks/gitleaks-action@v2
           env:
             GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
   ```
2. **Audit Parameters**:
   - `fetch-depth: 0`: Guarantees Gitleaks inspects all historical commits rather than just the PR tip.
   - `upload-sarif`: Routes SAST findings into the GitHub repository Security tab for triage and tracking.

> **Completion criterion**: CI workflow committed, running Gitleaks with `fetch-depth: 0` and uploading DevSkim SARIF findings to GitHub Security.

---

## Diagnostic Evaluation Scorecard

| # | Evaluation Axis | Diagnostic Inquiry | Passing Gate | Verification Method |
|---|---|---|---|---|
| 1 | **Dual-Scanner Partitioning** | Are SAST linting (DevSkim) and secret scanning (Gitleaks) split into specialized hooks? | Both hooks declared in config | Review `.pre-commit-config.yaml` |
| 2 | **Multi-File Dispatcher** | Does the setup handle multiple staged files without crashing on single-arg CLI limits? | Python loop wrapper active | Test with multiple staged files |
| 3 | **Deliberate Smoke Test** | Have both hooks been verified to block commits using deliberate synthetic failures? | Both SAST and secrets exit 1 | Smoke test with MD5 and test key |
| 4 | **Suppression Hygiene** | Are false positives handled via surgical inline comments rather than folder exclusions? | Zero blanket folder exclusions | Inspect config for broad excludes |
| 5 | **Dual-Gate CI Parity** | Does remote CI enforce full history secret checks (`fetch-depth: 0`) and SARIF reporting? | CI workflow active in PR gate | Verify `.github/workflows/security.yml` |

---

## Anti-Patterns

- **Secret-Linter Conflation** — Relying solely on DevSkim for secret detection, allowing subtle or high-entropy API tokens to leak into commits.
- **Whole-Repo Local Scanning** — Running `devskim analyze -I .` on every commit in a large repo, causing unacceptable developer latency and hook bypasses.
- **Blanket Directory Exclusions** — Masking false positives by excluding entire folders (e.g. `src/` or `tests/`) rather than suppressing specific rule IDs.
- **Client-Only Security Reliance** — Failing to enforce security checks in CI, allowing `git commit --no-verify` to push vulnerabilities directly to the remote repository.
- **Unverified Hook Deployment** — Rolling out pre-commit hooks without executing synthetic failure verification for both SAST and credential gates.
- **Real-Secret Verification** — Using actual production or test credentials to verify scanner blocking instead of synthetic high-entropy dummy strings.
