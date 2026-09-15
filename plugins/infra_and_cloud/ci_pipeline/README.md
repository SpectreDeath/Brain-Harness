# domain.ci_pipeline (v1.0.0)

CI/CD pipeline workflow linter, circular job dependency detector, and action security auditor

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/infra_and_cloud/ci_pipeline` |
| Category | `infra_and_cloud` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `validate_github_actions_workflow` | `(workflow_yaml)` | Validate GitHub Actions YAML workflow structure (name, on trigger, jobs, permissions) |
| `find_circular_job_dependencies` | `(jobs)` | Detect cyclic or broken 'needs:' dependencies across pipeline jobs |
| `audit_action_pins` | `(workflow_yaml)` | Audit third-party GitHub Actions for mutable tags (e.g. @v3) vs immutable commit SHA pins |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

CI/CD pipeline workflow validator and dependency auditor plugin.

#### Functions

- `def validate_github_actions_workflow(workflow_yaml) -> dict[str, Any]` — Validate structure of a GitHub Actions YAML workflow.
- `def find_circular_job_dependencies(jobs) -> dict[str, Any]` — Detect circular dependency cycles in job DAG.
- `def audit_action_pins(workflow_yaml) -> dict[str, Any]` — Audit third-party GitHub Action references for mutable tags vs immutable SHA pins.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.infra_and_cloud.ci_pipeline.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
