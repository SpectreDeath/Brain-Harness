# domain.docker_container (v1.0.0)

Docker container linter, multi-stage Dockerfile generator, and container security auditor

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/infra_and_cloud/docker_container` |
| Category | `infra_and_cloud` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `lint_dockerfile` | `(dockerfile_content)` | Lint Dockerfile for root user vulnerabilities, missing cache flags, latest tag usage, and security antipatterns |
| `generate_dockerfile` | `(runtime, entrypoint_command, port)` | Generate an optimized, production-ready multi-stage Dockerfile for a given language/runtime |
| `audit_container_security` | `(container_config)` | Audit container runtime configuration (privileged mode, read-only rootfs, capabilities, volume mounts) |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Docker container linter, multi-stage generator, and security auditor plugin.

#### Functions

- `def lint_dockerfile(dockerfile_content) -> dict[str, Any]` — Lint a Dockerfile for security and best practice issues.
- `def generate_dockerfile(runtime, entrypoint_command, port) -> dict[str, Any]` — Generate a hardened multi-stage Dockerfile.
- `def audit_container_security(container_config) -> dict[str, Any]` — Audit runtime configuration of a container.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.infra_and_cloud.docker_container.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
