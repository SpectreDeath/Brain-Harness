# domain.terraform_iac (v1.0.0)

Terraform / OpenTofu HCL parser, state drift detector, and cloud resource cost estimator

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/infra_and_cloud/terraform_iac` |
| Category | `infra_and_cloud` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `parse_hcl_blocks` | `(hcl_content)` | Parse Terraform HCL blocks (resource, variable, provider, output, module) from text |
| `detect_state_drift` | `(declared_state, actual_state)` | Compare declared Terraform resource attributes against actual cloud state |
| `estimate_resource_costs` | `(resources)` | Estimate monthly cloud infrastructure costs based on resource type heuristics |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Terraform / OpenTofu HCL parser, state drift detector, and cost estimator plugin.

#### Functions

- `def parse_hcl_blocks(hcl_content) -> dict[str, Any]` — Extract declared HCL blocks (resource, variable, provider, output, module).
- `def detect_state_drift(declared_state, actual_state) -> dict[str, Any]` — Compute drift diff between declared state and actual state.
- `def estimate_resource_costs(resources) -> dict[str, Any]` — Estimate monthly cloud infrastructure costs.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.infra_and_cloud.terraform_iac.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
