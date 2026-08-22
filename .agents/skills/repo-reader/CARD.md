# Summary Card: `repo-reader`

```
┌─────────────────────────────────────────────────────────────┐
│ SKILL: repo-reader                                          │
│ CATEGORY: Memory & Epistemics                               │
│ INVOCATION: Manual / Trigger Phrase                         │
│ TRIGGERS: "read repository", "connect repo", "introspect"  │
│ TARGET: Git Repository (Local Path or Remote GitHub URL)    │
└─────────────────────────────────────────────────────────────┘
```

---

## 5-Stage Progression

| Stage | Action | Primary Output | Gate / Checkpoint |
| :--- | :--- | :--- | :--- |
| **1. Attach & Detect** | Invoke `brain_attach(path/url, read_commits=True)` | Mounted repo in memory | Format identified (`git_repository`) |
| **2. 4-Axis Query** | Interrogate Architecture, Commits, Conventions, Deltas | Scored result sets | 4 query batches harvested |
| **3. Visual Brief** | Render HTML with Mermaid Architecture DAG & Timeline | `%TEMP%\repo-reader-*.html` | Clickable link delivered |
| **4. Checkpoint** | User review of candidate KIs | `RequestFeedback: true` | User approved items |
| **5. Lineage Commit**| Save KIs with Isnad provenance & commit citations | `.harness/knowledge/` | Zero unanchored claims |

---

## 4-Axis Introspection Matrix

1. **Architectural Topography**: Service keys, IoC containers, module boundaries, and entrypoint patterns.
2. **Commit Trajectories**: Commit evolution history, bug fixes, refactoring rationale, and breaking changes.
3. **Engineering Conventions**: Testing frameworks, type checking, CI workflows, and code hygiene.
4. **Delta Innovations**: Deep modules, novel algorithms, domain models, and high-leverage primitives.

---

## Invariants & Guardrails

- **Read-Only Lens**: Never mutate, overwrite, or commit files to the external repository.
- **Commit & Line Grounding**: Every extracted KI must include source file, line range, and Git commit hash.
- **Human-in-the-Loop**: Never commit persistent knowledge records without explicit user approval.
