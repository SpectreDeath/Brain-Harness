# Codebase Context Service

The `harness.services.codebase_context` subpackage provides multi-layer codebase instruction file verification, token budget enforcement, semantic path classification, and context drift governance across `AGENTS.md`, `CLAUDE.md`, and agent rule trees.

---

## Architectural Invariants

- **Typed Service Key (`Rule 2`)**: Resolved through `CODEBASE_CONTEXT_SERVICE_KEY` (`ServiceKey[CodebaseContextService]`) or `resolve_codebase_context(context)`.
- **Instruction Hygiene & Line Bounds (`Rule 11`)**: Enforces strict line limits (<150 lines), zero tutorial leakage, and explicit negative execution boundaries.
- **3-Tier Zero-Fork Configuration (`Rule 44`)**: Resolves operational rules and thresholds across default configs, repo configs, and runtime overrides via `ConfigResolver`.
- **Slotted Dataclass Architecture (`Rule 12`)**: High-frequency verification records (`TokenBudgetCheck`, `ContextSmellViolation`, `ContextGovernanceReport`) use `slots=True` and `frozen=True`.

---

## Module & Symbol Reference

| Module | Core Classes / Symbols | Description |
|---|---|---|
| [`protocol.py`](protocol.py) | `CodebaseContextService`, `CODEBASE_CONTEXT_SERVICE_KEY` | Typed service specification for instruction linting, budgeting, and context auditing. |
| [`service.py`](service.py) | `DefaultCodebaseContextService` | Default implementation orchestrating linter rules, config resolution, and governance audits. |
| [`resolvers.py`](resolvers.py) | `resolve_codebase_context` | Single-seam IoC container resolver returning active service or standalone fallback. |
| [`governor.py`](governor.py) | `ContextGovernor` | 5-stage context governance pipeline enforcing boundaries and drift detection. |
| [`linter.py`](linter.py) | `ContextLinter` | Fast syntax and diagnostic linter verifying token budgets and format rules. |
| [`classifier.py`](classifier.py) | `SemanticPathClassifier` | Path classifier partitioning files into domain scopes and execution tiers. |
| [`config.py`](config.py) | `ConfigResolver` | Cascading configuration loader honoring zero-fork standards. |
| [`manifest.py`](manifest.py) | `ManifestScriptInspector` | Polyglot manifest analyzer extracting entrypoints and script declarations. |
| [`checks.py`](checks.py) | `TokenBudgetCheck`, `PathIntegrityCheck`, `ScriptIntegrityCheck` | Slotted rule verification checks. |
| [`reports.py`](reports.py) | `ContextGovernanceReport`, `ContextSmellViolation`, `GovernanceStageResult` | Slotted diagnostic audit reports. |

---

## Usage Recipes

### Linting Repository Context Files
```python
from pathlib import Path
from harness.services.codebase_context import resolve_codebase_context

def verify_agent_instructions(workspace_root: Path):
    service = resolve_codebase_context()
    report = service.audit_workspace(workspace_root)
    if not report.passed:
        for violation in report.violations:
            print(f"[{violation.rule_name}] {violation.file_path}: {violation.message}")
```

### Checking Token Budget Ceilings
```python
from harness.services.codebase_context.linter import ContextLinter

linter = ContextLinter(max_tokens=4000)
result = linter.check_file_budget("AGENTS.md")
assert result.passed, f"AGENTS.md exceeds token quota: {result.token_count}"
```

