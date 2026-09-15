# domain.k8s_manifest (v1.0.0)

Kubernetes manifest linter, resource request/limit validator, and pod security context checker

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/infra_and_cloud/k8s_manifest` |
| Category | `infra_and_cloud` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `lint_k8s_manifest` | `(manifest_yaml)` | Lint Kubernetes YAML manifests for missing labels, deprecations, and missing namespaces |
| `validate_resource_limits` | `(manifest_yaml)` | Ensure CPU/memory requests and limits are explicitly declared on all container specs |
| `check_security_context` | `(manifest_yaml)` | Audit securityContext (runAsNonRoot, allowPrivilegeEscalation, drop capabilities) |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Kubernetes manifest linter, resource limit validator, and security auditor plugin.

#### Functions

- `def lint_k8s_manifest(manifest_yaml) -> dict[str, Any]` — Lint basic Kubernetes YAML manifest structure.
- `def validate_resource_limits(manifest_yaml) -> dict[str, Any]` — Check for CPU and memory resource requests & limits.
- `def check_security_context(manifest_yaml) -> dict[str, Any]` — Audit pod and container securityContext settings.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.infra_and_cloud.k8s_manifest.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
