# Skill Summary Card: `repo-reader`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ Name:        repo-reader                               │
│ Category:    memory / epistemics                       │
│ Invocation:  /repo-reader                              │
│ Trigger:     "read repository", "connect repo",        │
│              "introspect codebase", "commit evolution" │
│ Version:     1.0.0                                     │
│ Requires:    "brain_bridge"                            │
│ Provides:    "repo_introspection"                      │
├────────────────────────────────────────────────────────┤
│ Target:      Mount Git repo (local/remote) to distill  │
│              codebase seams & trajectories into KIs.   │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Repository Progression

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Attach & Detect** | Invoke `brain_attach(path/url, read_commits=True)` | Mounted repo in memory | Format identified (`git_repository`) |
| **2. 4-Axis Query** | Interrogate Architecture, Commits, Conventions, Deltas | Scored result sets | 4 query batches harvested |
| **3. Visual Brief** | Render HTML with Mermaid Architecture DAG & Timeline | `%TEMP%\repo-reader-*.html` | Dark-mode HTML brief delivered |
| **4. Checkpoint** | User review of candidate KIs | `implementation_plan.md` | `RequestFeedback: true` approved |
| **5. Lineage Commit**| Save KIs with Isnad provenance & commit citations | `.harness/knowledge/` | Zero unanchored claims |

---

## 4-Axis Introspection Matrix

1. **Architectural Topography**: Service keys, IoC containers, module boundaries, and entrypoint patterns.
2. **Commit Trajectories**: Commit evolution history, bug fixes, refactoring rationale, and breaking changes.
3. **Engineering Conventions**: Testing frameworks, type checking, CI workflows, and code hygiene.
4. **Delta Innovations**: Deep modules, novel algorithms, domain models, and high-leverage primitives.

---

## Anti-Patterns Cheat Sheet

- **Surface Code Scanning**: Reading file listings without querying deep module implementations or commit evolution.
- **Disconnected Commit Analysis**: Inspecting commit messages without correlating them to modified code files.
- **Foreign Repository Mutation**: Attempting to write, commit, or alter files in the external mounted repository.
- **Unanchored Seam Extrapolations**: Speculating on architectural intent without citing source lines and commit diffs.

---

## Invariants & Guardrails

- [ ] **Read-Only Lens**: Never mutate, overwrite, or commit files to the external repository.
- [ ] **Commit & Line Grounding**: Every extracted KI must include source file, line range, and Git commit hash.
- [ ] **Human-in-the-Loop**: Never commit persistent knowledge records without explicit user approval.
- [ ] **Visual Brief Delivery**: Always emit an interactive `%TEMP%` HTML report with Mermaid before finalizing.

