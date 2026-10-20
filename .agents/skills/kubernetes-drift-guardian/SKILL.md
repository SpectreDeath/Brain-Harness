---
name: kubernetes-drift-guardian
description: Detect, audit, and remediate Kubernetes resource manifest drift, RBAC least-privilege violations, and pod security standards. Do not use for generic local process management or unauthenticated cluster modification.
---

# Kubernetes Drift Guardian

The Kubernetes Drift Guardian audits live cluster states against declared GitOps manifests, detects configuration drift, enforces RBAC least-privilege security boundaries, and guards pod security standards across namespace workloads.

## Operational Workflow

1. **Manifest Parsing & AST Normalization**: Parse declared Helm charts and Kustomize overlays into canonical resource graphs.
2. **State Reconciliation**: Compare desired manifest states against live API server responses to isolate configuration drift.
3. **RBAC Boundary Auditing**: Analyze cluster role bindings, service accounts, and token automount settings for privilege escalation risks.
4. **Remediation Plan Formulation**: Scaffold deterministic YAML patches to reconcile live cluster states with repository source of truth.

## Anti-Patterns

- **Direct In-Cluster Hotfixing** — Mutating live cluster resources manually via `kubectl edit` without committing changes to GitOps source.
- **Wildcard RBAC Permissions** — Granting `*` verb permissions across all resource groups to simplify initial deployment.
- **Privileged Container Overuse** — Running container pods with `securityContext.privileged: true` without explicit cryptographic attestation.

## Diagnostic Verification

Verify Kubernetes manifest reconciliation and drift reports against cluster audit schemas using declarative manifest diffs.
