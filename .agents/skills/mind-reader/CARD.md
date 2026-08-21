# Summary Card: `mind-reader`

```
┌─────────────────────────────────────────────────────────────┐
│ SKILL: mind-reader                                          │
│ CATEGORY: Memory & Epistemics                               │
│ INVOCATION: Manual / Trigger Phrase                         │
│ TRIGGERS: "read brain", "introspect brain", "learn from"   │
│ TARGET: External Brain / IDE Session / Knowledge Folder     │
└─────────────────────────────────────────────────────────────┘
```

---

## 5-Stage Progression

| Stage | Action | Primary Output | Gate / Checkpoint |
| :--- | :--- | :--- | :--- |
| **1. Attach & Detect** | Invoke `brain_attach(path)` | Mounted store in memory | Format identified & valid |
| **2. 4-Axis Query** | Interrogate Logic, Errors, Habits, Deltas | Scored result sets | 4 query batches harvested |
| **3. Visual Brief** | Render HTML with Mermaid DAG | `%TEMP%\mind-reader-*.html` | Clickable link delivered |
| **4. Checkpoint** | User review of candidate KIs | `RequestFeedback: true` | User approved items |
| **5. Lineage Commit**| Save KIs with Isnad provenance | `.harness/knowledge/` | Zero unanchored claims |

---

## 4-Axis Introspection Matrix

1. **Architectural Logic**: Why decisions, service keys, and boundaries were formed.
2. **Error Trajectories**: Failed commands, tool errors, and recovery strategies.
3. **Epistemic Habits**: Coding standards, verification routines, and recurring patterns.
4. **Delta Learnings**: Surprising techniques and novel paradigm discoveries.

---

## Invariants & Guardrails

- **Read-Only Lens**: Never mutate, overwrite, or delete files inside the external target brain directory.
- **Isnad Grounding**: Every extracted KI must include source file and line/step coordinates.
- **Human-in-the-Loop**: Never commit persistent memory records without explicit user approval checkpoint.
