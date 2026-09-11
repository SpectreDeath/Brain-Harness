# Deep-Skill Forge: Stage-by-Stage Reference Guide

## Overview

The `deep-skill-forge` pipeline coordinates three foundational workflows into a single autonomous progression:
1. Literature Ingestion & Extraction (`book-to-skill-forge`)
2. Deep Architecture Refactoring (`deepen-architecture`)
3. Epistemic Learning & Retention (`epistemic-memory-lifecycle`)

---

## The 5 Stages

### Stage 1: Literature Ingestion & Deconstruction
- **Input**: Markdown file, textbook chapter, technical paper, or lecture transcript.
- **Actions**:
  - Strip narrative filler, rhetorical flourishes, and autobiographical anecdotes.
  - Formulate the 4-Axis Literature Matrix:
    - *Axis 1*: Semantic activation verbs & negative boundary clause.
    - *Axis 2*: Concrete Shu operational progression (3 to 5 steps).
    - *Axis 3*: Diagnostic coaching scorecards with quantitative passing gates.
    - *Axis 4*: Explicit named anti-patterns with positive invariant rules.
- **Gate**: Complete 4-axis matrix formulated.

### Stage 2: Deep Architecture & Domain Synthesis
- **Input**: Formulated 4-axis framework from Stage 1.
- **Actions**:
  - Model internal entity states using `@dataclass(slots=True, frozen=True)` (Rule 12).
  - Design polyglot manifest handling across languages (`package.json`, `pyproject.toml`, `Makefile`).
  - Configure 3-tier zero-fork configuration (`config.default.yaml`, Rule 44).
  - Design headless Click CLI subcommands (`harness <domain> ...`, Rule 10).
- **Gate**: Architecture blueprint and domain model interfaces finalized.

### Stage 3: Consolidated Master Checkpoint
- **Input**: Architecture blueprint and literature extraction.
- **Actions**:
  - Render an interactive HTML visual brief in `%TEMP%` loading Tailwind CSS and Mermaid.js via CDN.
  - Present `implementation_plan.md` artifact with `RequestFeedback: true`.
  - **STOP and wait for user review and approval**.
- **Gate**: Explicit user approval received at the consolidated checkpoint.

### Stage 4: Scaffold, Test & Bounded In-Flight Self-Repair
- **Input**: Approved implementation plan.
- **Actions**:
  - Scaffold skill package (`SKILL.md`, `CARD.md`, `config.default.yaml`, `scripts/`, `references/`).
  - Author contract test suite (`tests/test_<skill_name>.py`).
  - Execute automated tests (`pytest`).
  - If tests fail, run in-flight repair loop up to **3 attempts maximum** before escalating.
- **Gate**: 100% test pass rate across unit, integration, and ecosystem hygiene checks.

### Stage 5: Epistemic Learning & Knowledge Graph Commit
- **Input**: Passing skill package and test suite.
- **Actions**:
  - Scaffold canonical dual-file directory under `.harness/knowledge/<ki_id>/` with `metadata.json` and `summary.md` (Rule 40).
  - Register skill in `CONTEXT-MAP.md` under the appropriate bounded domain.
  - Index new skill and semantic triggers into the active Skill Knowledge Graph.
- **Gate**: Knowledge Vault item committed, `CONTEXT-MAP.md` updated, and graph indexed.
