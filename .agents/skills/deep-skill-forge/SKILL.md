---
name: deep-skill-forge
description: Execute autonomous end-to-end literature-to-deep-skill synthesis, architectural deepening, and epistemic knowledge retention. Scaffolds deep modules with slotted domain models, bounded self-repair, and Knowledge Vault commits. Do not use for generic prompt writing or single-turn system prompt edits.
---

# Deep-Skill Forge: Literature, Architecture & Knowledge Synthesis

`deep-skill-forge` is the authoritative meta-skill pipeline that transforms intellectual literature—non-fiction books, technical articles, frameworks, and research papers—into production-grade, architecturally deepened AI agent skills and Knowledge Vault items.

It fuses three essential engineering disciplines:
1. **Literature Deconstruction & Shu-Ha-Ri Extraction** ([`book-to-skill-forge`](../book-to-skill-forge/SKILL.md))
2. **Deep Module Architecture & Seam Elevation** ([`deepen-architecture`](../deepen-architecture/SKILL.md))
3. **Epistemic Learning & Knowledge Vault Retention** ([`epistemic-memory-lifecycle`](../epistemic-memory-lifecycle/SKILL.md))

See [CARD.md](CARD.md) for the companion summary card, 5-stage progression matrix, and invariants checklist.
Consult `/agent-skills-architect` for progressive disclosure standards, [pipeline-stages.md](references/pipeline-stages.md) for pipeline stages, and [isnad-lineage.md](references/isnad-lineage.md) for isnad claim traceability.

---

## The 5-Stage Deep-Skill Pipeline Progression

```
[1. Literature Deconstruction] ──► [2. Deep Architecture Synthesis] ──► [3. Consolidated Master Checkpoint]
                                                                                   │
                                                                                   ▼
[5. Epistemic Learn & Graph Commit] ◄── [4. Scaffold, Test & 3-Attempt Self-Repair] ◄────┘
```

---

## 1. Literature Ingestion & Deconstruction

Deconstruct intellectual literature into high-density procedural models without context flooding:

1. **Ingest & Cleanse Source Content**:
   - Ingest markdown notes, articles, or transcripts from local paths or URLs.
   - Strip narrative fluff, biographical anecdotes, and marketing prose.
2. **Extract the 4-Axis Literature Matrix**:
   - **Axis 1 (Trigger Bounds)**: Identify precise semantic activation verbs and explicit negative deflection boundaries (`Do not use for...`).
   - **Axis 2 (The Shu Stage)**: Formulate 3 to 5 discrete, sequential operational stages with binary completion criteria.
   - **Axis 3 (Coaching Scorecards)**: Extract diagnostic interview questions and quantitative pass/fail evaluation tables.
   - **Axis 4 (Anti-Patterns)**: Formulate named failure modes paired with mandatory invariant rules.

> **Completion criterion**: 4-axis literature matrix formulated with triggers, Shu steps, scorecards, and anti-patterns isolated.

---

## 2. Deep Architecture & Domain Synthesis

Synthesize the target skill's internal architecture into deep, high-leverage modules before authoring files:

1. **Slotted & Frozen Dataclass Architecture (Rule 12)**:
   - Design `@dataclass(slots=True, frozen=True)` domain models for all internal state entities, validation results, and check records.
   - Assert construction invariants in `__post_init__` to guarantee immutable value objects.
2. **Polyglot Manifest & Extensible Tooling**:
   - Avoid hardcoded tool assumptions; inspect project manifests across languages (`package.json`, `pyproject.toml`, `Makefile`, `Cargo.toml`).
3. **3-Tier Zero-Fork Configuration (Rule 44)**:
   - Define baseline operational parameters in `config.default.yaml`.
   - Support layered overrides: Project Override (`.agents/skills.config.yaml`) $\rightarrow$ Skill Default $\rightarrow$ Fallback.
4. **Headless Click CLI Seams (Rule 10)**:
   - Wire core capabilities into headless Click CLI subcommands (`harness <domain> ...`) with formatted tables and JSON outputs.

> **Completion criterion**: Deep module architecture, slotted domain models, zero-fork config, and headless CLI seams specified.

---

## 3. Consolidated Master Checkpoint

Provide decision-ready visual transparency and enforce human-in-the-loop governance:

1. **Render the Visual Master Brief**:
   - Generate a self-contained HTML visual brief in `%TEMP%\deep-skill-forge-<timestamp>.html`.
   - Theme: Dark mode (`#0d1117`), Tailwind CSS, and Mermaid.js via CDN.
   - Display the end-to-end pipeline DAG, before/after architecture topology diagrams, diagnostic scorecards, and anti-pattern matrices.
   - Surface the absolute clickable path to the user.
2. **Present Single Consolidated Implementation Plan**:
   - Author an `implementation_plan.md` artifact detailing:
     - Target skill name, location, and bounded description.
     - 5-stage progression with binary completion gates.
     - Slotted domain models, bundled scripts, and test contracts.
     - Planned Knowledge Vault item ID and isnad lineage claims.
   - Set `RequestFeedback: true` in artifact metadata.
   - **STOP and wait for explicit user approval** before generating or modifying files.

> **Completion criterion**: Visual brief rendered in %TEMP% and user approval received at the consolidated master checkpoint.

---

## 4. Scaffold, Test & Bounded In-Flight Self-Repair

Author the complete skill package, execute automated tests, and resolve failures autonomously:

1. **Scaffold the Skill Package**:
   - Author `SKILL.md` (< 500 lines, Rule 44 description, Rule 37 anti-patterns).
   - Author `CARD.md` (single-pipe ASCII borders `│`, `SKILL:` header, stage table, invariants).
   - Author `config.default.yaml` (operational budgets and zero-fork schema).
   - Author bundled scripts under `scripts/` (PEP 723 metadata, UTF-8 streams, non-interactive).
   - Author contract test suite under `tests/test_<skill_name>.py`.
2. **Execute Automated Verification Suite**:
   - Run `pytest tests/test_<skill_name>.py -v`.
   - Run `pytest tests/test_skills_hygiene.py -k "TestSkillsEcosystemHygiene" -v`.
3. **Enforce the Bounded In-Flight Self-Repair Loop**:
   - If tests fail, do NOT abandon the run or immediately ask the user.
   - Capture exact error diagnostics and tracebacks.
   - Apply targeted in-flight code and test contract repairs.
   - Re-run the test suite.
   - **Hard Circuit Breaker**: Limit self-repair to a maximum of **3 attempts**. If unresolved after 3 tries, halt and present diagnostics to user.

> **Completion criterion**: Skill package authored, 100% test pass rate achieved, and self-repair circuit breaker respected.

---

## 5. Epistemic Learning & Knowledge Graph Commit

Commit synthesized intelligence to persistent memory and register routing edges:

1. **Author Canonical Knowledge Vault Dual-Files (Rule 40)**:
   - Create `.harness/knowledge/<ki_id>/` containing:
     - `metadata.json`: Schema, title, source isnad attribution, SHA-256 hashes, timestamped claims list.
     - `summary.md`: Epistemic introspection, mental models, decision heuristics, and anti-pattern defenses.
2. **Update Ecosystem Context Map**:
   - Register the new skill under the appropriate bounded domain in `CONTEXT-MAP.md`.
3. **Index into Skill Knowledge Graph**:
   - Execute `harness skills graph` to register the new skill node, semantic triggers, and cross-skill dependency edges.

> **Completion criterion**: Knowledge Vault dual-files written, CONTEXT-MAP.md updated, and skill graph indexed.

---

## The Three Foundational Pillars

### 1. The Visual Brief Pillar
Every deep skill forging run must render an interactive HTML visual brief in `%TEMP%` displaying the literature source, pipeline stages, deep architecture topology, and diagnostic scorecards.

### 2. The Mandatory Checkpoint Pillar
The agent must never author skill files or mutate persistent memory without first presenting `implementation_plan.md` with `RequestFeedback: true` and awaiting explicit user confirmation.

### 3. Explicit Anti-Patterns
Rigid architectural boundaries prevent superficial summaries, brittle scripts, and ungrounded memory drift.

---

## Anti-Patterns

- **Superficial Summarization** — Emitting passive prose summaries instead of actionable, deep-module agent instructions with binary completion gates.
- **Shallow Script Sprawl** — Bundling untyped procedural scripts instead of slotted/frozen domain models and high-leverage engine abstractions.
- **Bypassing Consolidated Checkpoint** — Mutating workspace files or authoring skills without explicit user approval on the master implementation plan.
- **Infinite Repair Thrashing** — Retrying failing tests in an unbounded loop without an explicit circuit-breaker limit of 3 attempts.
- **Single-File Vault Pollution** — Dumping single flat JSON files into `.harness/knowledge/` instead of the canonical dual-file directory (`metadata.json` + `summary.md`).
- **Unregistered Orphan Skills** — Scaffolding skill directories without updating `CONTEXT-MAP.md` or indexing into the active Skill Knowledge Graph.
