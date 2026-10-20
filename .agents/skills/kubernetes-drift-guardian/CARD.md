```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:        kubernetes-drift-guardian                │
│ Category:     infra_and_cloud                          │
│ Invocation:   /kubernetes-drift-guardian               │
│ Triggers:     "k8s drift", "kubernetes audit", "rbac", │
│               "manifest drift", "pod security"         │
│ Version:      1.0.0                                    │
│ Isolation:    subprocess                               │
│ Provides:     "service.k8s_drift"                      │
├────────────────────────────────────────────────────────┤
│ Target:       Detect, audit, and remediate Kubernetes  │
│               resource manifest drift and RBAC least-  │
│               privilege policy violations.             │
└────────────────────────────────────────────────────────┘
```

# Kubernetes Drift Guardian — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
| --- | --- | --- | --- |
| **1. Manifest Parse** | Ingest declared Kubernetes manifests and Helm specs | `declared_ast.json` | Valid Kubernetes resource schemas |
| **2. Live Scrape** | Fetch active cluster state via API server client | `live_state.json` | Sanitized cluster resource snapshot |
| **3. Drift Comparison**| Compute structural diff between declared and live | `drift_report.json` | Categorized drift (added, modified, removed) |
| **4. Patch Proposal** | Generate declarative patch to restore desired state | `remediation_patch.yaml`| Valid strategic merge patch |

---

## Mandatory Invariants Checklist

- [ ] **GitOps Source of Truth Invariant**: The repository manifest is always authoritative; live states must reconcile to Git.
- [ ] **Least Privilege Invariant**: Service account bindings must restrict API group access to declared operational scopes.
- [ ] **Air-Gapped Safety Invariant**: Drift calculations must execute offline against static snapshots without unauthenticated API calls.
- [ ] **Slotted Immutability Invariant**: Drift reports and reconciliation records must use slotted frozen dataclasses.
