# The Three-Layer Context Architecture

## Background & Problem Statement

Coding agents operate within a finite attention buffer known as the **Context Window**. As a development session progresses, this buffer fills with:
- System prompts and tool definitions (~12,000 tokens)
- Root context files loaded at session start (~1,000 - 5,000 tokens)
- Source code files inspected by the agent (~9,000 tokens)
- Test executions and terminal stack traces (~3,500 tokens)

When context files are oversized, the agent experiences **Context Rot** (Anthropic): the model's ability to recall and adhere to specific instructions sharply degrades as total token count climbs. 

Furthermore, context files that are inlined into every turn compete directly with the stack traces and source code the agent needs to read in order to solve the problem.

---

## The Three Layers

The architecture partitions repository context across three distinct layers characterized by different loading frequencies and token costs:

```
┌─────────────────────────────────────────────────────────────┐
│                 THE THREE CONTEXT LAYERS                    │
├─────────────────────────────────────────────────────────────┤
│ 1. Always Loaded Root (AGENTS.md)                           │
│    - Read on every turn / session start                     │
│    - Budget: <= 800 tokens (~3,200 chars)                   │
│    - Essential commands & repo-wide invariants only         │
├─────────────────────────────────────────────────────────────┤
│ 2. Scoped Subdirectories (src/AGENTS.md, .cursor/rules/)    │
│    - Loaded only when working within a subtree / glob       │
│    - Budget: <= 400 tokens (~1,600 chars)                   │
│    - Domain-specific handler shapes & local contracts       │
├─────────────────────────────────────────────────────────────┤
│ 3. On-Demand Pointers (docs/, skills/, decisions/)          │
│    - Root file holds only 4-5 path links (~20 tokens)       │
│    - Heavy documents (ADRs, schemas, workflows) loaded      │
│      only when the agent explicitly navigates to them       │
└─────────────────────────────────────────────────────────────┘
```

### Layer 1: The Always-Loaded Root (`AGENTS.md`)
- **Cost**: Paid on *every single request* across the repository.
- **Budget**: Strictly $\le 800$ tokens. You should be able to read it aloud in under one minute.
- **Content Criteria**:
  - Exact build/test/install commands that cannot be guessed.
  - Conventions that differ from the language or framework defaults.
  - The single source of truth notice and definition of done.
  - Pointers to Layer 3 documents.
- **The Removal Test**:
  > *"Would removing this line cause the agent to make a mistake?"*
  If the answer is no, delete the line immediately.

### Layer 2: The Scoped Subdirectory Layer
- **Cost**: Paid only when the agent works inside that directory or edits matching files.
- **Location**: Nested `AGENTS.md` (e.g. `src/AGENTS.md`, `tests/AGENTS.md`) or Cursor `.cursor/rules/*.mdc`.
- **Precedence**: Nested context sits *on top of* the root file; rules closest to the edited file take precedence.
- **Content Criteria**:
  - Input validation conventions and error return shapes.
  - Subsystem isolation boundaries (e.g. "handlers never touch the database store directly").
  - Test fixture reset requirements (e.g. "call `resetTasks()` in `beforeEach`").

### Layer 3: The On-Demand Pointer Layer
- **Cost**: Almost zero token overhead at startup (~20-50 tokens for path lists).
- **Location**: `docs/architecture.md`, `docs/decisions/XXXX.md`, `.agents/skills/<name>/SKILL.md`.
- **Content Criteria**:
  - Architecture Decision Records (ADRs) explaining *why* choices were made.
  - Deliberate absences: Explaining that missing infrastructure (e.g. no database, zero dependencies) is intentional to prevent agents from speculatively adding them.
  - Complex step-by-step procedures (e.g. adding an endpoint, running migrations).

---

## Inclusion Heuristic Matrix

| Include in Context Files | Leave Out / Move to docs/ |
|---|---|
| Commands the agent cannot guess (`npm test`, `pytest`) | Basic tutorials (e.g. "React is a UI library") |
| Non-obvious conventions (in-memory store, zero deps) | Standard language features (`const` vs `var`) |
| Negative boundaries ("handlers never touch store") | Vague encouragement ("write clean code") |
| Worked example pointers (`src/api/tasks.js`) | Multi-page API specifications (use links) |
| Deliberate absences in ADRs ("do not add ORM") | Temporary sprint goals or sprint history |
