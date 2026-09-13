```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: repo-triad-forge                                              │
│ Category: engineering / meta-skills                                  │
│ Version: 1.0.0                                                       │
│ Invocation: /repo-triad-forge                                        │
│ Triggers: "repo triad forge", "audit and forge", "repo to triad",    │
│           "external repo pipeline", "repo cognitive bridge"          │
│ Requires: "deep-repo-auditor", "deep-skill-forge",                   │
│           "repo-to-plugin-forge", "epistemic-memory-lifecycle"       │
│ Target: Unified repo audit, KI retention, skill & plugin forging     │
└──────────────────────────────────────────────────────────────────────┘
```

# Repo-Triad Forge — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Pre-Flight & 5D** | Inspect repo topology & compute complexity | Structural Inspection Report | Languages, packages & compute tier mapped |
| **Stage 2: Multi-Axis Audit** | 5-stage codebase audit & visual briefs | 5 HTML Briefs in `%TEMP%` | Interactive HTML visual briefs rendered |
| **Stage 3: Vault Checkpoint** | Formulate isnad claims & prompt checkpoint | Dual-file KIs in `.harness/` | User approval via `ask_question` & KIs committed |
| **Stage 4: Skill & Plugin** | Scaffold slotted skill & sandboxed plugin | Skill & Plugin packages | Slotted models, `PluginValidator` & `ServiceKey` |
| **Stage 5: Test & Register** | Bounded self-repair & ecosystem sync | Passing tests & Context Map | 100% tests green, graph indexed, map updated |

---

## Vocabulary & Levers

- **The Cognitive Triad**: Unification of multi-axis codebase archaeology, deep skill synthesis, and sandboxed plugin creation.
- **Dual-File Knowledge Vault (Rule 40)**: Writing canonical `metadata.json` + `summary.md` under `.harness/knowledge/<ki_id>/`.
- **Subprocess Sandbox Isolation (Rule 5, 14)**: Isolating untrusted external plugins in subprocess transports with explicit pipe drainage in `finally` blocks.
- **Slotted/Frozen Dataclass Architecture (Rule 12, 43)**: Enforcing immutable value objects and memory-efficient data modeling.
- **Bounded In-Flight Self-Repair**: Circuit-breaker loop resolving test failures within $\le 3$ automated repair attempts.
- **Plugin Module Singleton (Rule 45)**: Exporting instantiated `plugin = MyPlugin()` singleton for dynamic discovery.

---

## Mandatory Invariants Checklist

- [ ] **Interactive User Checkpoint**: Never persist Knowledge Items or write skills without explicit user approval.
- [ ] **Subprocess Sandbox Default**: External plugins must run in subprocess isolation with Rule 14 pipe cleanup.
- [ ] **Slotted & Frozen Models**: High-volume domain entities must declare `slots=True, frozen=True` (Rule 12).
- [ ] **Canonical Dual-File Vault**: Knowledge items must be written as directory with `metadata.json` and `summary.md` (Rule 40).
- [ ] **Bounded Self-Repair Limit**: Test failure self-repairs must halt at $\le 3$ attempts before escalating.
- [ ] **Complete Ecosystem Sync**: Every run must update `CONTEXT-MAP.md` and reindex the Skill Knowledge Graph.
