# Infrastructure & Cloud Domain Architecture

The Infrastructure & Cloud domain governs container lifecycle management, Kubernetes manifest validation, Infrastructure-as-Code (IaC) linting, and automated delivery pipelines.

---

## Domain Scope & Boundaries

This domain manages operational runtime environments, container sandboxes, and cloud infrastructure:
- In Scope: OCI container management, Kubernetes manifest verification, Terraform/OpenTofu HCL validation, and CI/CD workflow pipeline orchestration.
- Out of Scope: Internal micro-kernel subprocess isolation (Kernel / Plugins), in-memory service dependency DAGs (Kernel), or application-level code refactoring (Software Engineering).

---

## Ubiquitous Language & Core Terminology

- **Container Manager**: A runtime interface that manages isolated OCI container lifecycles, volume mounts, and network port bindings. (*Avoid*: Docker wrapper, sandbox host)
- **Manifest Validator**: A static schema checker that asserts structural compliance and resource limit specifications for Kubernetes YAML objects. (*Avoid*: K8s linter, YAML checker)
- **Infrastructure Spec**: A declarative Terraform HCL or OpenTofu definition specifying cloud resources, security groups, and ingress policies. (*Avoid*: IaC script, deployment file)
- **Pipeline**: A directed workflow definition specifying build, test, and container packaging stages for CI/CD automation. (*Avoid*: Action script, build job)

---

## Architectural Invariants & Patterns

- Subprocess Isolation by Default (Rule 5): External runtime dependencies and sandboxed tools must execute in dedicated isolated processes or containers.
- Windows Asyncio Proactor Loopback (Rule 56): When network isolation (`HARNESS_NO_NETWORK=1`) is enforced in runners, local loopback sockets (`127.0.0.1`, `::1`) must remain accessible for internal Windows Proactor self-pipes.
- Zero-Fork Operational Budgets (Rule 44): Infrastructure and runtime plugins provide co-located `config.default.yaml` defining baseline operational budgets (timeouts, resource limits).

---

## Co-Located Plugins & Micro-Kernel Services

- Plugin Sandbox Subsystem: [`src/harness/plugins/sandbox.py`](../../../src/harness/plugins/sandbox.py) providing process sandboxes and venv staging.
- System Diagnostics Service: [`src/harness/commands/system.py`](../../../src/harness/commands/system.py) providing system resource and host environment telemetry.

---

## Associated Agent Skills

- [`agent-harness-architect`](../../../.agents/skills/agent-harness-architect/SKILL.md): Architects and sandboxes production agent harnesses and runtime loops.
- [`ai-native-harness-engineer`](../../../.agents/skills/ai-native-harness-engineer/SKILL.md): Governs 4-gate behavioral pipelines and credential-free MCP security.
