# Scoped CI Formatting & Epistemic Hygiene Gates (Axis 3)

## Invariant
- Scope `ruff format --check` in `.github/workflows/ci.yml` strictly to hardened core packages (`kernel`, `brain_bridge`, `deep_auditor`, `harness_spawner`, `dock`, `commands/reflection`) instead of churn-reformatting legacy files.
- Run `mypy src/harness/kernel --ignore-missing-imports`, `python -m harness.cli context lint`, and `python -m harness.cli knowledge sync --strict` on the primary Ubuntu Python 3.11 runner.
