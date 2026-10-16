# CARD: plugin-seam-and-mirror-auditor

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SKILL: plugin-seam-and-mirror-auditor                                       │
│ CATEGORY: Verification & Seam Audit                                         │
│ INVOCATION: /plugin-seam-and-mirror-auditor                                 │
│ TRIGGERS: "audit plugins", "fuzz parameters", "check documentation mirror", │
│           "plugin seam verification", "sync plugin readme", "auto-fix docs" │
│ TARGET: Multi-axis plugin auditing, parameter fuzzing, and doc-sync         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5-Stage Progression Matrix

| Stage | Focus Area | Primary Artifact / Mechanism | Passing Completion Gate |
| :--- | :--- | :--- | :--- |
| **1. Target Discovery** | Path & Manifest Scanning | Target inspection summary | Discovers all plugins within target dir (single or recursive). |
| **2. IoC DAG Audit** | Topological Ordering & Cycles | Service dependency graph | 0 circular dependencies; 0 dangling `ServiceKey` requirements. |
| **3. AST Mirror Audit** | Documentation & Manifest Drift | Signature mismatch report | Every entrypoint in code documented; parameter names matched. |
| **4. Auto-Fix Remediation** | Documentation & Manifest Sync | Updated READMEs & manifests | Scaffolded missing READMEs; aligned tables with AST signatures. |
| **5. Adversarial Fuzzing** | Runtime Resilience & Timeouts | Fuzz findings report | 0 timeouts (>5.0s); 0 unhandled `asyncio.run()` loop collisions. |

---

## The Three Core Pillars

```
┌─────────────────────────────────────────────────────────────┐
│ 1. AST AS SOURCE OF TRUTH                                   │
│ - Never manually edit README tables or guess parameters.    │
│ - Extract ground-truth function signatures via Python AST.  │
├─────────────────────────────────────────────────────────────┤
│ 2. RESILIENT ASYNC CONFINEMENT                              │
│ - Never invoke asyncio.run() inside running event loops.    │
│ - Enforce strict 5.0s execution bounds on all fuzz vectors. │
├─────────────────────────────────────────────────────────────┤
│ 3. PATH-AGNOSTIC AUTO-REMEDIATION                           │
│ - Support single plugin dirs, category dirs, and monorepos. │
│ - Scaffold standard Diátaxis documentation and sync tables. │
└─────────────────────────────────────────────────────────────┘
```

---

## Mandatory Invariants Checklist

- [ ] **Path Flexibility Verified**: Script operates seamlessly on single plugin dirs, category dirs, or workspace roots without hardcoded path assumptions.
- [ ] **Windows UTF-8 Stream Codec**: Standard streams explicitly reconfigured to UTF-8 per `Rule 23`.
- [ ] **Subprocess Pipe Transport Disposal**: All async subprocess executions explicitly close pipes inside `finally` blocks per `Rule 14`.
- [ ] **Slotted Data Models**: Internal audit findings and target representations use `slots=True` per `Rule 12`.
- [ ] **AST Source-of-Truth**: Python function signatures in `main.py` serve as the immutable ground truth for documentation synchronization.
