---
name: architecture-deepening-workflow
description: Orchestrate the 7-phase architecture deepening cycle to decompose monolithic hotspots into subpackages <= 200 lines with contract tests and visual briefs. Do not use for superficial linting or single-line bug fixes.
---

# Architecture Deepening Workflow

Authoritative operational orchestration skill for executing systematic architecture deepening cycles across monolithic hotspots in the Brain Harness repository.

## Overview

The `architecture-deepening-workflow` codifies the empirical 7-phase protocol perfected across 70 continuous deepening cycles:
1. **Hotspot Mining**: Scans repository for monolithic files (> 200 LOC, Rule 11), filtering noise roots (`.git`, `__pycache__`, untracked GEV).
2. **AST Seam Mapping**: Traces upstream callers, downstream imports, Click command groups, IoC service keys, and test contracts.
3. **Subpackage Modularization**: Factors monolithic code into fine-grained subpackages where every file is $\le 200$ LOC, equipped with slotted domain models (Rule 12), single-seam resolvers (Rule 58), and Click single-source consolidation (Rule 6).
4. **Contract Verification**: Authors and executes strict contract tests (`tests/test_<name>_decomposition.py`) and verifies zero ruff lint errors.
5. **Interactive Visual Master Brief**: Generates standalone dark-mode HTML visual review briefs in `%TEMP%`.
6. **Multi-Cycle Regression Gate**: Executes the cumulative multi-cycle regression suite (1,000+ tests) with Windows proactor background guards.
7. **Secure Token-Redacted Git Push**: Stages only cycle files and pushes with in-memory token redaction (Rule 15).

## Dependencies

- [`monolith-decomposition-engine`](../monolith-decomposition-engine/SKILL.md) — AST seam factorization, slotted models, and single-seam resolvers.
- [`adversarial-agent-verifier`](../adversarial-agent-verifier/SKILL.md) — Harsh adversarial test review and DAG seam verification.
- [`agent-skill-sdlc`](../agent-skill-sdlc/SKILL.md) — 3-tier zero-fork configuration and validation lifecycle.

## Utility Scripts

The skill provides a multi-command CLI helper under `scripts/deepen_cycle.py`:

```bash
# 1. Scan for monolithic candidates > 200 lines
python scripts/deepen_cycle.py scan --threshold 200 --output scan_results.json

# 2. Plan submodule breakdown for a specific target
python scripts/deepen_cycle.py plan --target src/harness/commands/plugins.py --output plan.json

# 3. Check line count limits across submodules in a directory
python scripts/deepen_cycle.py check-lines --dir src/harness/commands/plugins/ --max-lines 200

# 4. Run contract verification and lint checks
python scripts/deepen_cycle.py verify --test tests/test_plugins_decomposition.py --lint-target src/harness/commands/plugins/

# 5. Synthesize interactive HTML visual review brief
python scripts/deepen_cycle.py brief --cycle 71 --title "Plugin Commands Decomposition" --output-html %TEMP%\review.html

# 6. Execute full multi-cycle regression gate
python scripts/deepen_cycle.py regression --script scratch/run_full_cycle_regression.py

# 7. Securely commit and push with token redaction
python scripts/deepen_cycle.py push --cycle 71 --message "refactor(cycle-71): decompose plugin commands" --files src/harness/commands/plugins/ tests/test_plugins_decomposition.py
```

---

## Mandatory Checkpoint Gates

Before committing or staging any architecture deepening cycle artifacts, assert all gates:
1. **Gate 1 (LOC Enforcement)**: Assert every factored submodule file is ≤ 200 lines with `check-lines` subcommand.
2. **Gate 2 (Contract Test Pass)**: Assert all `tests/test_*_decomposition.py` contracts pass with zero failures.
3. **Gate 3 (Regression Gate)**: Execute the full cumulative multi-cycle regression suite before push. Do not bypass via `--no-tests`.
4. **Gate 4 (User Approval for Push)**: Request explicit user review via `RequestFeedback: true` before executing the secure token-redacted git push step.

---

## Anti-Patterns

- **Premature Submodule Bloat** — Leaving factored submodules above 200 lines in violation of Rule 11.
- **Untracked File Staging** — Executing `git add .` or touching untracked external files (e.g. Gods Eye View) instead of explicit cycle file lists.
- **Bypassing Regression Gates** — Committing or pushing changes without running the full cumulative regression suite.
- **Leaking Secrets in Git Arguments** — Interpolating tokens directly into shell strings instead of isolated Python runner scripts with in-memory redaction (Rule 15).
- **Silent Batch Exception Masking** — Using bare `except Exception: continue` without logging or reraising programming errors (Rule 32).
