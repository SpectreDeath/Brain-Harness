```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: context-anti-rot-sync                                         │
│ SKILL: context-anti-rot-sync                                          │
│ Category: software_engineering / context_architecture               │
│ Version: 1.0.0                                                       │
│ Invocation: /context-anti-rot-sync                                   │
│ Triggers: "context anti rot sync", "clean context", "audit agents md"│
│           "sync context files", "enforce line limits", "linter check"│
│           "run context sync"                                         │
│ Requires: "codebase-context-governor",                               │
│           "codebase-context-architect",                              │
│           "agent-instruction-architect",                             │
│           "compute-model-assessor"                                   │
│ Target: Automated codebase context hygiene, single-source sync & test│
└──────────────────────────────────────────────────────────────────────┘
```

# Context Anti-Rot Sync — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Context Rot & Line Audit** | Scan instruction files for bloat, line count overflow & lint leakage | Audit JSON Report | Violations detected & token budgets cataloged |
| **Stage 2: Deterministic Cleanse** | Deduplicate whitespace, prune tutorial prose & enforce negative bounds | Cleaned Text Buffer | File line count bounded $\le 150$ lines |
| **Stage 3: Single-Source Synchronization** | Project canonical rules into client-specific instruction files | Synchronized Targets | Derived files updated with zero semantic drift |
| **Stage 4: Mandatory Checkpoint Gate** | Present audit report and proposed diffs for user confirmation | Implementation Plan | Explicit user confirmation received |
| **Stage 5: Automated Anti-Rot Linting** | Execute CI checks for frontmatter budgets, links & delimiters | Lint Diagnostic Report | 100% CI linter rules pass with zero criticals |

---

## Vocabulary & Levers

- **Context Rot**: Degradation of agent reasoning caused by stale instructions, outdated commands, or bloated context.
- **Rule 11 Line Budget**: Strict mandate keeping repository instruction files (`AGENTS.md`, `CLAUDE.md`) under 150 lines.
- **Lint Leakage**: The anti-pattern of copying transient linter or compiler errors into persistent instruction files.
- **Single Source of Truth (SSOT)**: Deriving client instruction files deterministically from canonical workspace manifests.
- **Negative Boundaries**: Explicit, non-negotiable declarations of "what NOT to touch" to bound agent blast radius.
- **Dual-Tier Frontmatter Budget**: Strict YAML description bound between 100 and 350 characters (Rule 44).

---

## Mandatory Invariants Checklist

- [ ] **Instruction File Budget Guard**: Target instruction files must never exceed 150 lines (Rule 11).
- [ ] **Zero Transient Lint Leakage**: Persisted instruction files must never contain transient compiler or linter errors.
- [ ] **Explicit Negative Boundary Enforcement**: Every instruction file must define unambiguous "what NOT to touch" boundaries.
- [ ] **Deterministic File-Based JSON Output**: All CLI inspection subcommands must write structured JSON to `--output` (Rule 4).
- [ ] **Zero-Fork Operational Config**: Configuration overrides must resolve against `config.default.yaml` without repo forks (Rule 44).
