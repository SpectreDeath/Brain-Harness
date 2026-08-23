# Skill Summary Card: `mind-reader`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        mind-reader                               │
│ Category:    memory / epistemics                       │
│ Invocation:  /mind-reader                              │
│ Trigger:     "read brain", "introspect brain",         │
│              "learn from trajectories", "distill brain"│
│ Version:     1.0.0                                     │
│ Requires:    "brain_bridge"                            │
│ Provides:    "brain_introspection"                     │
├────────────────────────────────────────────────────────┤
│ Target:      Attach to external brain / IDE session    │
│              to distill trajectories into grounded KIs.│
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Introspection Progression

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Attach & Detect** | Invoke `brain_attach(path)` | Mounted store in memory | Format identified & classified |
| **2. 4-Axis Query** | Interrogate Logic, Errors, Habits, Deltas | Scored result sets | 4 query batches harvested |
| **3. Visual Brief** | Render HTML with Mermaid DAG | `%TEMP%\mind-reader-*.html` | Dark-mode HTML brief delivered |
| **4. Checkpoint** | User review of candidate KIs | `implementation_plan.md` | `RequestFeedback: true` approved |
| **5. Lineage Commit**| Save KIs with Isnad provenance | `.harness/knowledge/` | Zero unanchored claims |

---

## 4-Axis Introspection Matrix

1. **Architectural Logic**: Why decisions, service keys, and boundaries were formed.
2. **Error Trajectories**: Failed commands, tool errors, and recovery strategies.
3. **Epistemic Habits**: Coding standards, verification routines, and recurring patterns.
4. **Delta Learnings**: Surprising techniques and novel paradigm discoveries.

---

## Anti-Patterns Cheat Sheet

- **Passive Ingestion**: Mounting a brain without interrogating error recovery trajectories.
- **Unanchored KI Commits**: Writing learned items without exact file and transcript line citations.
- **Foreign Brain Mutation**: Writing modified state back into an external target directory.
- **Surface Scraping**: Only reading file headers without querying conversational reasoning steps.

---

## Invariants & Guardrails

- [ ] **Read-Only Lens**: Never mutate, overwrite, or delete files inside the external target brain directory.
- [ ] **Isnad Grounding**: Every extracted KI must include source file and line/step coordinates.
- [ ] **Human-in-the-Loop**: Never commit persistent memory records without explicit user approval checkpoint.
- [ ] **Visual Brief Delivery**: Always emit an interactive `%TEMP%` HTML report with Mermaid before finalizing.

