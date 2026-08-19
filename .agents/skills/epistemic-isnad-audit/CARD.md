# Skill Summary Card: `epistemic-isnad-audit`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        epistemic-isnad-audit                     │
│ Category:    epistemic-governance / memory             │
│ Invocation:  /epistemic-isnad-audit                    │
│ Trigger:     "epistemic audit", "verify isnad",        │
│              "check claim lineage", "audit provenance" │
│ Version:     1.0.0                                     │
├────────────────────────────────────────────────────────┤
│ Target:      Enforce unbroken chain-of-custody         │
│              provenance on all factual assertions      │
│              prior to persistent memory / state commit.│
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Isnad Audit Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Empty Mind Extraction** | Extract raw atomic claims without evaluative bias | Raw claim list | Zero interpretive or speculative commentary |
| **2. Isnad Lineage Tracing** | Map each claim to primary source, test, or manifest | Provenance audit table | 100% of claims classified (Verified vs. Hypothesis) |
| **3. Visual Lineage Brief** | Render interactive HTML lineage DAG in `%TEMP%` | `%TEMP%\isnad-audit-*.html` | Dark-mode lineage graph delivered |
| **4. Verification Gate** | Resolve hypotheses via active inspection tools | `implementation_plan.md` | `RequestFeedback: true` approved by user |
| **5. Isnad Commit** | Persist verified decisions with structured Isnad block | `.context/decisions.md` | Structured JSON isnad block written |

---

## Lineage Node Types Cheat Sheet

```
┌─────────────────────────────────────────────────────────────────┐
│                     ISNAD NODE TYPES                            │
├────────────────────────────────┬────────────────────────────────┤
│ Primary Code Source            │ [file.py:L10-L25](file:///...) │
├────────────────────────────────┼────────────────────────────────┤
│ Deterministic Tool Execution   │ RunCommand(evt_id=...)         │
├────────────────────────────────┼────────────────────────────────┤
│ Declarative Manifest           │ pyproject.toml / plugin.json   │
└────────────────────────────────┴────────────────────────────────┘
```

---

## Verification & Quality Checklist

- [ ] **Zero Floating Assertions**: Every core proposition has an unambiguous file/event link.
- [ ] **Empty Mind Compliance**: Extraction is completed prior to evaluation or synthesis.
- [ ] **Visual Lineage Brief Present**: Interactive HTML written to `%TEMP%` and delivered to user.
- [ ] **Mandatory Checkpoint Passed**: User signs off on `implementation_plan.md` with resolved hypotheses.
