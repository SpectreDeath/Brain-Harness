---
name: elephant-goldfish-governor
description: Govern AI agent design and review workflows using the Elephant-Goldfish bifurcated context architecture, artifact-first spec drafting, 5-stage antagonistic review gates, and living spec drift detection. Do not use for superficial prompt drafting, single-turn ungrounded chat, or small one-line bug fixes.
---

# Elephant-Goldfish Governor — Spec-Driven Architecture & Zero-Context Review

`elephant-goldfish-governor` operationalizes the Elephant-Goldfish Model (EGM) within the Brain Harness. It enforces bifurcated cognitive contexts: pairing a deep-context drafting partner (The Elephant) with isolated, zero-context subagent reviewers (The Goldfish) to eliminate hallucination cascades, confirmation bias, and conversational context pollution.

See [CARD.md](CARD.md) for companion summary card, stage progression table, and invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline operational budgets and timeout thresholds.

---

## The 5-Stage EGM Governance Progression

```
[1. Upstream Concept Ideation & Multi-Lens Brainstorm]
                       │
                       ▼
[2. Sectional Spec Drafting & Semantic Boundary Isolation]
  ├── FeatureRange (High-altitude architecture & simplicity)
  └── DetailedRange (Low-altitude signatures, tests & rollout)
                       │
                       ▼
[3. Five-Stage Antagonistic Goldfish Review Pipeline]
  ├── Stage 5: Initial Zoom Out Review (Simplicity & YAGNI)
  ├── Stage 6: Naive Comprehension Test (Self-containment)
  ├── Stage 7: Technical Critic Review (Scale & failure modes)
  ├── Stage 8: Intermediate Zoom Out (Creep regression check)
  └── Stage 9: Implementation Readiness (Concreteness & tests)
                       │
                       ▼
[4. In-Thread Finding Remediation & Tri-State Gating]
  └── Resolve blockers/majors in Elephant context before coding
                       │
                       ▼
[5. Continuous Living Spec Drift Detection & AST Auditing]
  └── Compare checked-in docs/designs/*.md vs live codebase symbols
```

---

## 1. Upstream Concept Ideation & Multi-Lens Brainstorm

Transform raw concepts into anchored working hypotheses without premature implementation:

1. **Conduct Open-Ended Clarification**:
   - Interview the engineer across multiple conversational turns to extract the core hypothesis, constraints, and non-goals.
   - Strictly prohibit multiple-choice crutches during exploratory ideation.
2. **Spawn Multi-Lens Goldfish Brainstorm Swarm**:
   - Dispatch parallel zero-context reviewers across 6 lenses: Skeptical Architect, UX/Ergonomics, Performance/Scale, Security/Failure, Codebase Reuse, and Structural Integrity.
   - Aggregate, deduplicate, and compile findings into `concepts_brief.md`.
3. **Artifact-First Delivery**:
   - Never dump brainstorm summaries into the chat window. Write directly to `concepts_brief.md` and present clean path references.

> **Completion criterion**: Working hypothesis anchored, 6-lens brainstorm executed, and verified `concepts_brief.md` emitted to disk.

---

## 2. Sectional Spec Drafting & Semantic Boundary Isolation

Compile verified briefs into disciplined technical specifications with strict altitude control:

1. **Establish Semantic Range Boundaries**:
   - `FeatureRange`: High-level architecture, user journeys, root problem focus, simplicity (YAGNI), and rejected alternatives.
   - `DetailedRange`: Concrete file paths, class/function signatures, error types, test cases, and phased rollout plans.
2. **Iterative Section Drafting**:
   - Draft the specification section by section into `docs/designs/<feature>.md`, pausing after each section for human feedback.
   - Prevent the "Weeds Syndrome" by strictly barring implementation code from high-level architecture sections.

> **Completion criterion**: Specification compiled into `docs/designs/<feature>.md` with clean semantic boundary isolation between FeatureRange and DetailedRange.

---

## 3. Five-Stage Antagonistic Goldfish Review Pipeline

Execute sequential zero-context verification with specialized rubrics:

1. **Initial Zoom Out Review (Stage 5)**:
   - Evaluate root-problem focus, YAGNI, simplicity, and codebase reuse against `zoom-out-standard.md`.
2. **Naive Comprehension Test (Stage 6)**:
   - Verify self-containment with an isolated reader subagent without prior context or tribal knowledge.
3. **Technical Critic Review (Stage 7)**:
   - Stress-test system design, race conditions, scaling limits, and edge cases against `feature-spec-standard.md`.
4. **Intermediate Zoom Out (Stage 8)**:
   - Re-audit additions made during Comprehension and Critic stages to eliminate newly introduced scope creep.
5. **Implementation Readiness Test (Stage 9)**:
   - Audit exact file paths, symbol signatures, test fixtures, and migration plans against `implementation-readiness-standard.md`.

> **Completion criterion**: All 5 review stages executed with normalized findings grouped into Blocker, Major, and Nit severities.

---

## 4. In-Thread Finding Remediation & Tri-State Gating

Enforce human-in-the-loop decision rights and immediate spec patching:

1. **Tri-State Checkpoint Gates**:
   - At each review phase, present standard choices: proceed to next stage, resolve findings with agent in-thread, edit manually, or pause.
2. **In-Thread Resolution**:
   - The primary Elephant agent evaluates findings, drafts concrete text patches, and applies approved edits directly to the design document.
   - Recalculate line boundaries after patches are applied.

> **Completion criterion**: All blockers and major findings resolved and confirmed by the human engineer before implementation begins.

---

## 5. Continuous Living Spec Drift Detection & AST Auditing

Prevent specification rot by treating checked-in designs as living ground-truth contracts:

1. **AST Codebase Extraction**:
   - Scan target source directories for classes, functions, dataclasses, and routes mentioned in `docs/designs/*.md`.
2. **Differential Drift Categorization**:
   - Classify discrepancies into 4 categories:
     - `Missing Features`: Logic promised in the spec but absent in code.
     - `Incomplete Models`: Dataclasses/structs missing declared fields.
     - `Logic Shortcuts`: Hardcoded stubs or mocks replacing dynamic flows.
     - `Architectural Divergence`: Unauthorized libraries or misplaced logic.
3. **Emit Actionable Drift Reports**:
   - Produce `{YYYY-MM-DD}_DRIFT_REPORT.md` reporting strictly divergences without reciting conforming code.

> **Completion criterion**: Comprehensive differential drift report generated identifying all discrepancies between checked-in specs and codebase reality.

---

## The Three Foundational Pillars

### 1. Asymmetric Cognitive Context Bifurcation
Never allow the same LLM context that drafts code to validate its own work. Split development into a deep-context author (Elephant) and zero-context isolated reviewers (Goldfish).

### 2. Artifact-First Delivery & Altitude Boundaries
Banish chat dumps. Emitting large specs or review logs into chat panes causes context bloat and user fatigue. Partition documents into high-altitude architecture (`FeatureRange`) and low-altitude implementation (`DetailedRange`).

### 3. Living Ground-Truth Specifications
Design specifications checked into `docs/designs/` are permanent engineering contracts. Regularly audit code against specs via automated AST drift detection to guarantee architectural fidelity.

---

## Anti-Patterns

- **Single-Thread Self-Review** — Allowing the authoring agent to review its own design in the same conversational context without fresh subagents.
- **Chat Dump Spew** — Dumping multi-page specifications or lengthy review logs directly into the chat pane instead of persistent markdown artifacts.
- **Altitude Inversion (Weeds Syndrome)** — Smuggling helper functions, raw SQL queries, or loop variables into high-level architecture sections before validating root problem fit.
- **Sycophantic Glazing** — Reviewers praising proposals with empty flattery ("great idea", "brilliant approach") instead of leading with technical failure modes.
- **Specification Rot Abandonment** — Allowing checked-in design documents to decay as code evolves without running automated drift detection.
- **Silent Reviewer Swallowing** — Treating timed-out or failed reviewer subagents as passing with zero findings instead of marking them as `not run`.

