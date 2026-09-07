# AI-Assisted Codebase Archaeology & Characterization Testing Before Refactoring

**ID:** `ki_self_20260905_08`  
**Category:** `software_architecture`  
**Origin:** `Hugo Teijiz / freeCodeCamp Literature`  
**Provenance Lineage:** `https://www.freecodecamp.org/news/understand-a-legacy-codebase-with-ai/`, `https://www.freecodecamp.org/news/characterization-tests-before-refactoring-legacy-code/`, `D:/markdown from chrome/freeCodeCamp/Refactoring/`, `AGENTS.md#Rule41`

## Executive Summary

This Knowledge Item captures the foundational mental models, heuristic rules, and architectural invariants distilled from Hugo Teijiz's dual treatises on legacy modernization. When engineers inherit legacy codebases, the natural impulse is immediate improvement—cleaning up nested conditions, removing duplicated calculations, or introducing modern architectural layers. However, legacy code frequently encodes crucial implicit knowledge: strange conditions represent historical production patches, duplicated calculations represent independently evolving business domains, and cryptic columns form part of unversioned external contracts.

This distillation establishes the core engineering invariant: **Never change legacy software before capturing its observable behavior today.** AI coding assistants accelerate this process not by writing replacement code, but by serving as experimental inquiry tools to map repositories, trace capability paths, disentangle business rules from infrastructure, and design characterization safety nets.

## Epistemic Mental Models & Architectural Invariants

### 1. Codebase Archaeology Precedes Modernization
- **The Solution Trap**: Prompts like *"Rewrite using Clean Architecture"* or *"Find bad code"* embed premature solutions before understanding what the system actually does.
- **The Invariant Sequence**:
  $$\text{What exists?} \longrightarrow \text{Why does it exist?} \longrightarrow \text{What behavior matters?} \longrightarrow \text{What is uncertain?} \longrightarrow \text{What should change?}$$
- **Capability Bounding**: Always bound archaeology to a single, concrete capability (e.g. `Approve Order`). Modernizing whole applications at once guarantees context overflow and undetected regressions.

### 2. The 5-Level Evidence Validation Hierarchy
AI explanations of legacy code can sound authoritative while being fundamentally incomplete. Every architectural conclusion must be corroborated against this hierarchy:
1. **Repository Search & AST**: Confirm invocations, call hierarchies, and reference counts (`rg`).
2. **Existing Tests & Fixtures**: Extract historical edge assumptions and fixture shapes.
3. **Database Schema**: Audit nullability, foreign keys, default values, and legacy fields.
4. **Production Observability**: Check logs and telemetry to verify whether paths are live.
5. **Git Blame & Commit History**: Inspect historical commits (`git log -S`) to discover the operational rationale behind unusual logic.

### 3. Characterization Tests as Temporary Knowledge Infrastructure
- **Definition**: A characterization test documents what the software *does today*, not what it *should do*.
- **The AI Hallucination Invariant**: Never allow AI to invent expected behavior. If code contains `age > 65`, AI often assumes the business rule is `age >= 65`. Expected values must be derived strictly from executable runs, fixtures, or database snapshots.
- **Side Effect Primacy**: Assert meaningful external side effects (database writes, emitted events, published queue messages, audit logs) rather than merely checking return values.
- **Seam Minimality**: When coupling blocks testing, introduce minimal mechanical seams (parameterized repository/client interfaces) without altering business logic.

### 4. Defect Quarantine Protocol
- When characterization tests expose obvious defects (e.g. charging a fee for zero-dollar transactions), distinguish **discovered behavior** from **intentional behavior change**.
- Lock the current behavior in tests first. Do **not** fix bugs during a refactoring branch. Downstream consumers may depend on the historical quirk. Document the defect, seek stakeholder clarification, and repair it in a dedicated commit.

### 5. Micro-Step Refactoring & Test Maturation
- Execute refactorings in atomic micro-steps (single transformation $\rightarrow$ run suite $\rightarrow$ commit).
- As business understanding solidifies, graduate temporary characterization tests into permanent domain specification tests.
