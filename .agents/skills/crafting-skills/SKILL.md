---
name: crafting-skills
description: Design, author, or refactor agent skills using high-precision craft standards. Use when creating a new skill from scratch, upgrading an existing skill to deep-module standards, or generating companion summary cards (CARD.md) with visual briefs and mandatory checkpoints.
---

# Skill Crafting & Refactoring Engine

`crafting-skills` is the authoritative specification and refactoring engine for agent skills. It designs, authors, and refactors skills into high-precision, deep-module blueprints that produce deterministic, high-leverage agent workflows.

Every skill authored or refactored under this engine incorporates three foundational pillars:
1. **The Visual Brief** — Interactive HTML reports in `%TEMP%` with Tailwind and Mermaid diagrams for decision-ready visual review.
2. **The Mandatory Checkpoint** — Explicit human-in-the-loop gates (`RequestFeedback: true`) preventing unapproved or destructive action.
3. **Explicit Anti-Patterns** — Rigid behavioral boundaries that eliminate speculative abstractions, interface churn, and premature completion.

See [CARD.md](CARD.md) for the skill summary card, quick-reference template, and completion criteria checklist.
Consult `/writing-for-agents` for the underlying information hierarchy, leading words, and cognitive load theory.

---

## The 5-Stage Skill Authoring & Refactoring Loop

Whether crafting a new skill or refactoring an existing one, execute this progression:

```
[1. Target & Seams] → [2. Information Hierarchy] → [3. Core Mechanics] → [4. Companion Card] → [5. Verification]
```

### Stage 1: Target & Seams (Domain & Triggers)

Define the exact operational boundary and invocation conditions:
- **Skill Name**: Short, kebab-case verb or gerund (`deepen-architecture`, `diagnosing-bugs`, `domain-modeling`).
- **Frontmatter Description**: Front-load the leading trigger words. State the exact case the skill handles with zero fluff. One trigger per branch; eliminate synonyms.
- **Seam Definition**: What public interfaces, files, or lifecycle boundaries does the skill operate upon?

> **Completion criterion**: Frontmatter written with tight trigger bounds and agreed operating seams.

---

### Stage 2: Information Hierarchy & Progressive Disclosure

Structure the skill content across the information hierarchy:

1. **Steps (Ordered Actions)**: The sequential stages of the skill. Each step must terminate on a crisp, checkable **completion criterion** that distinguishes done from not-done.
2. **In-File Reference**: Grouped rules, definitions, and invariant sets placed below the sequence (co-located).
3. **Disclosed Reference**: Push secondary templates, schemas, and summary cards into companion files (`CARD.md`, `REFERENCE.md`) behind context pointers.

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Frontmatter (name, description context pointer)          │
├─────────────────────────────────────────────────────────────┤
│ 2. Core Execution Sequence (Numbered stages + criteria)     │
│    - Stage 1: Analyze / Audit                               │
│    - Stage 2: Assess / Formulate                            │
│    - Stage 3: The Visual Brief (Temp HTML + Mermaid)        │
│    - Stage 4: Mandatory Checkpoint (Plan + Approval)        │
│    - Stage 5: Execution & Verification                      │
│    - Stage 6: Recording & Walkthrough                       │
├─────────────────────────────────────────────────────────────┤
│ 3. In-File Reference (Vocabulary, Levers, Guidelines)       │
├─────────────────────────────────────────────────────────────┤
│ 4. Anti-Patterns & Guardrails (Explicitly named boundaries) │
└─────────────────────────────────────────────────────────────┘
```

> **Completion criterion**: Document structured with clear separation between sequential steps and reference material.

---

### Stage 3: The Three Core Mechanics

Every high-performance skill must implement these three mechanisms:

#### A. The Visual Brief
For any non-trivial analysis, design review, or refactoring recommendation, text diffs are insufficient. The skill must instruct the agent to generate an interactive, self-contained HTML brief:
- **Location**: Write to `%TEMP%\<skill-name>-review-<timestamp>.html` (Windows) or `/tmp/<skill-name>-review-<timestamp>.html` (Unix).
- **Styling**: Load Tailwind CSS and Mermaid.js via CDN in a sleek dark theme (`#0d1117`).
- **Topology**: Render clear **Before vs. After** Mermaid diagrams showing architectural/workflow shifts.
- **Delivery**: Surface the absolute file path with clickable links to the user.

#### B. The Mandatory Checkpoint
Prevent the failure mode where agents dive into massive, breaking changes without consensus:
- Enforce generating an `implementation_plan.md` artifact before touching source code.
- Explicitly set `RequestFeedback: true` in artifact metadata.
- Require the agent to **STOP and wait** for explicit user approval before executing any destructive or modifying commands.

#### C. Explicit Anti-Patterns
Define named, concrete anti-patterns directly in the skill to establish rigid behavioral guardrails:
- Name the exact failure mode (e.g., *Speculative Abstraction*, *Interface Churn*, *Premature Completion*, *Horizontal Slicing*).
- State the telltale symptom and the required positive corrective behavior.

> **Completion criterion**: Skill body includes explicit sections for Visual Brief generation, Mandatory Checkpoint gating, and named Anti-Patterns.

---

### Stage 4: The Companion Summary Card (`CARD.md`)

Every skill must be paired with a co-located `CARD.md` file:
- **ASCII Summary Box**: Name, Category, Invocation, Trigger phrases, Target.
- **Stage Progression Table**: High-level stages, primary artifacts, and completion gates.
- **Vocabulary & Levers Cheat Sheet**: Compact definitions of leading words used in the skill.
- **Invariants & Guardrails**: Hard rules that apply on every turn.

> **Completion criterion**: `CARD.md` authored, co-located in the skill folder, and referenced from `SKILL.md`.

---

### Stage 5: Verification & Refactoring Audit

When authoring a new skill or refactoring an existing one, run this validation checklist:

1. **Positive Phrasing**: Are negative instructions replaced with positive target behaviors? (Avoid "don't do X"; use "do Y instead").
2. **Leading Words Check**: Are wordy paragraphs collapsed into pretrained concepts (*seam*, *depth*, *leverage*, *locality*, *brief*, *checkpoint*, *tracer bullet*, *push right*)?
3. **Premature Completion Resistance**: Are completion criteria checkable and exhaustive?
4. **Sediment & No-Ops Purge**: Are default model behaviors, obsolete config restatements, or conversational padding purged?

> **Completion criterion**: Skill passes all 4 verification checks with zero bloat and 100% actionable guidance.

---

## Refactoring Recipe: Upgrading an Existing Skill

When asked to refactor an existing skill:

1. **Read & Extract**: Inspect the source skill. Identify its core sequence, implicit assumptions, and domain vocabulary.
2. **Identify Friction**: Spot vague completion gates, missing human-in-the-loop checkpoints, raw text diff dumps, and negative prohibitions.
3. **Restructure**: Apply the 5-Stage Authoring standard. Add the Visual Brief (Temp HTML), Mandatory Checkpoint (`RequestFeedback: true`), and explicit Anti-Patterns.
4. **Scaffold `CARD.md`**: Generate the companion summary card with the ASCII header and stage table.
5. **Cross-Link**: Link `CARD.md` from `SKILL.md` and verify progressive disclosure.

---

## Anti-Patterns in Skill Authoring

- **Conversational Padding** — Opening with pleasantries, meta-commentary ("In this skill we will..."), or conversational filler. Start directly with the specification.
- **Negation Overrun** — Steering by prohibition ("Don't forget to...", "Never write..."). State the positive target behavior instead.
- **Vague Completion Gates** — Using subjective bounds ("Ensure code is good", "Understand the system") that invite premature completion. Use testable, binary bounds ("Full pytest suite passes green with 100% rate").
- **Unbounded Autonomy** — Letting agents execute breaking refactors without a formal `implementation_plan.md` checkpoint.
- **Monolithic Bloat** — Dumping 500 lines of reference in `SKILL.md` instead of disclosing secondary reference in companion markdown files (`CARD.md`, `REFERENCE.md`).
