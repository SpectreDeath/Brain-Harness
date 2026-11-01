# Skill Summary Card: `mantis-security-review`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:        mantis-security-review                   │
│ Category:     security_and_forensics                   │
│ Invocation:   /mantis-security-review                  │
│ Trigger:      "security review", "mantis review",      │
│               "exploit chaining", "dedupe ladder",     │
│               "ast taint audit", "review gate"         │
│ Version:      1.0.0                                    │
│ Requires:     "pre-commit-security-guard"              │
│ Provides:     "mantis_security_review", "triage"       │
├────────────────────────────────────────────────────────┤
│ Target:       10-stage autonomous security reviews,    │
│               hotspot history scans, AST taint audits, │
│               deduplication, and exploit chaining      │
└────────────────────────────────────────────────────────┘
```

---

## The 10-Stage Mantis Review Pipeline

| Stage | Command | Objective | Output Gate |
|---|---|---|---|
| **1. History Scan** | `harness mantis history-scan` | VCS churn and security commits | Discovered hotspots list |
| **2. Dir Summary** | `harness mantis dir-summary` | Structural surface mapping | Attack surface ratio |
| **3. Plan Review** | `harness mantis plan-review` | Threat model alignment | Scoped review target paths |
| **4. AST Audit** | `harness mantis audit` | Syntax & AST taint analysis | Candidate findings list |
| **5. Dedupe** | `harness mantis dedupe` | Syntactic & AST deduplication | Normalized findings |
| **6. Critic Filter**| `harness mantis critic-filter` | False-positive screening | Confidence-rated findings |
| **7. Review Gate** | `harness mantis gate` | CI threshold enforcement | Gate PASS / exit 1 |
| **8. Chaining** | `harness mantis chain-exploits` | Multi-step exploit chaining | Compound exploit graphs |
| **9. Calibrate** | `harness mantis calibrate-risk` | Asset & blast radius rating | Composite risk score |
| **10. Report** | `harness mantis report` | Dossier & remediation plan | Exported audit report |

---

## Mandatory Invariants Checklist

- [ ] **History Grounding Precedence**: Never conduct static code audits in isolation without surveying recent VCS commit churn and security fix histories.
- [ ] **Dual-Tier Deduplication**: All candidate findings must pass through syntactic hash and AST structure deduplication ladders before risk scoring.
- [ ] **Critic Confidence Threshold**: Findings evaluated by the critic filter must score confidence >= 0.70 before promotion to release gates.
- [ ] **Stepwise Gate Failures**: When `harness mantis gate` encounters findings exceeding `--fail-on` threshold, it must exit non-zero for CI interception.

---

## Cross-Skill References

- [rea-reverse-engineering](../rea-reverse-engineering/SKILL.md) — Binary and managed runtime artifact dissection.
- [differential-facet-verifier](../differential-facet-verifier/SKILL.md) — Multi-provider differential observation comparison.
- [reconstruction-obligation-ledger](../reconstruction-obligation-ledger/SKILL.md) — Cryptographic evidence sealing and obligation tracking.
- [pre-commit-security-guard](../pre-commit-security-guard/SKILL.md) — Left-shifted pre-commit security interception.
- [ethical-hacker-networking](../ethical-hacker-networking/SKILL.md) — Network protocol reconnaissance and fault isolation.

