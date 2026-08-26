---
name: harness-reflector
description: Reflect on, introspect, and extract foundational learnings from the Harness's own history, HTML architecture reports, transcripts, execution logs, and walkthroughs. Use when the user asks to reflect on past work, learn from internal reports or chat logs, distill heuristics from past cycles, run an endogenous memory reflection loop, or update the Knowledge Vault from internal history.
---

# Harness Reflector: Endogenous Memory & Metacognitive Distillation Engine

`harness-reflector` is the autobiographical reflection engine for Brain Harness. Operating atop internal execution history (HTML visual briefs in `%TEMP%`, conversation transcripts in `<appDataDir>\brain\*\logs\`, walkthroughs, and event logs), it reconstructs episodic developmental trajectories, extracts battle-tested invariants and failure modes, and commits verifiable, Isnad-grounded Knowledge Items (KIs) into the persistent Knowledge Vault.

Every endogenous memory reflection session executes this five-stage progression:

```
[1. Harvest Ephemeral Residue] → [2. 4-Axis Distillation] → [3. Visual Reflection Brief] → [4. Mandatory Checkpoint] → [5. Vault Lineage Commit]
```

See [CARD.md](CARD.md) for the companion summary card, 4-axis prompt matrix, and invariants checklist.
Consult `/crafting-skills` for authoring standards, `/epistemic-isnad-audit` for chain-of-custody lineage rules, and `/mind-reader` for foreign brain introspection.

---

## 1. Harvest Ephemeral Residue

Discover and harvest internal execution artifacts across the host environment:

1. **Harvest Temporary HTML Visual Briefs (`%TEMP%` / `$env:TEMP`)**:
   - Locate files matching `*architecture-review*.html`, `*compute-assessor*.html`, `*brief*.html`, and `*harness*.html`.
   - Extract titles, creation timestamps, Mermaid before/after diagrams, and explicit friction/gotcha callouts.
2. **Harvest Conversation Transcripts (`transcript.jsonl`)**:
   - Scan `<appDataDir>\brain\*\.system_generated\logs\transcript.jsonl`.
   - Ingest user intent, tool invocation sequences, runtime exceptions, test failure traces, and recovery adaptations.
3. **Harvest Walkthroughs & Plans**:
   - Ingest `walkthrough.md` and `implementation_plan.md` from recent workspace and brain trajectory folders.

> **Completion criterion**: Reports, transcripts, and walkthroughs indexed with file paths, timestamps, and extracted friction tokens.

---

## 2. 4-Axis Distillation & Cross-Correlation

Execute four structured reflection analyses across the harvested internal memory surface:

```
┌─────────────────────────────────────────────────────────────┐
│              4-AXIS ENDOGENOUS REFLECTION                   │
├──────────────────────────────┬──────────────────────────────┤
│ Axis 1: Architectural Seams  │ Axis 2: Error Trajectories   │
│ - Lifecycle staging choices  │ - Windows venv test timeouts │
│ - IoC service boundaries     │ - Shadowed CLI group bugs    │
├──────────────────────────────┼──────────────────────────────┤
│ Axis 3: Performance & Budget │ Axis 4: Actionable Invariants│
│ - Model tiering & thinking   │ - Rigid rules for future runs│
│ - Async timeout isolation    │ - Grounded Isnad provenance  │
└──────────────────────────────┴──────────────────────────────┘
```

1. **Axis 1 (Architectural Seams & Lifecycle)**:
   - Query: *"What architectural decisions or lifecycle staging patterns were proven effective or required refactoring?"*
   - Example insight: Lazy staging of sandboxed external plugins prevents startup cold-start penalties while keeping discovery instant.
2. **Axis 2 (Error Trajectories & Recoveries)**:
   - Query: *"What specific runtime exceptions, platform quirks (e.g. Windows venv creation), or CLI collisions caused failures, and how were they resolved?"*
   - Example insight: Click CLI groups must be declared exactly once in a single co-located block.
3. **Axis 3 (Performance & Compute Calibration)**:
   - Query: *"How did model thinking budgets and tool execution timeouts impact overall velocity and reliability?"*
   - Example insight: Tool execution inside `StepExecutionEngine` requires ACID context transactions with automatic disposal on failure.
4. **Axis 4 (Actionable Invariants & Anti-Patterns)**:
   - Formulate explicit, negative-constrained anti-patterns paired with positive invariant rules.

> **Completion criterion**: Candidate heuristics synthesized with confidence ratings and empirical grounding evidence.

---

## 3. The Visual Reflection Brief

Before committing changes to persistent storage, generate a self-contained, interactive HTML reflection brief:

- **Location**: Write to `%TEMP%\harness-reflection-<timestamp>.html` (Windows) or `/tmp/harness-reflection-<timestamp>.html` (Unix).
- **Styling**: Sleek dark theme (`#0d1117`) loading Tailwind CSS and Mermaid.js via CDN.
- **Topology**: Render the **Memory Ingestion & Isnad Lineage Topology** Mermaid DAG illustrating the path from ephemeral logs to persistent vault items.
- **Matrix**: Display the **Distilled Architectural Invariants & Heuristics** table with category badges, actionable rules, and source grounding.
- **Delivery**: Output the absolute file path with clickable links to the user.

> **Completion criterion**: Visual brief written to `%TEMP%`, verified non-empty, and clickable link presented.

---

## 4. Mandatory Checkpoint Gate

Prevent ungrounded or speculative mutations to the repository's ground-truth Knowledge Vault:

1. Formulate the distilled Knowledge Items (KIs) with their respective `IsnadLineageBlock` claims.
2. Present a summary of candidate KIs to the user with titles, categories, and evidence sources.
3. **STOP and wait** for explicit user review (`RequestFeedback: true`) before persisting to `.harness/knowledge/` or modifying workspace rules.

> **Completion criterion**: Human review checkpoint recorded before vault persistence.

---

## 5. Grounded Isnad Lineage & Vault Commit

Upon confirmation, commit the distilled learnings into the persistent Harness knowledge base:

1. **Construct Canonical `KnowledgeItemRecord`**:
   - Set `id`: `ki_self_YYYYMMDD_XX` (e.g., `ki_self_20260826_01`).
   - Populate `isnad.claims` with exact provenance nodes pointing to the source HTML brief, transcript log, or Git commit hash.
   - Populate `tags`: `[category, "endogenous_memory", "self_reflection"]`.
2. **Commit to Knowledge Vault**:
   - Save via `storage.save_knowledge_item(item)`.
   - Export to dual-file on-disk directory `.harness/knowledge/<ki_id>/` (`metadata.json` + summary).
3. **Update Knowledge Graph**:
   - Re-index with `harness.services.skill_graph` or `index_skills_cmd` so that subsequent agent planning loops immediately leverage the new memories.

> **Completion criterion**: Knowledge Items persisted in vault, on-disk dual files written, and isnad chain verified.

---

## Anti-Patterns

- **Amnestic Execution** — Repeating past mistakes (e.g. eager subprocess startup) across consecutive cycles without checking the Knowledge Vault.
- **Ungrounded Speculation** — Creating KIs based on theoretical ideals rather than actual execution evidence from reports and logs.
- **Silent Discard** — Letting rich temporary HTML reports sit in `%TEMP%` and expire unindexed.
- **Premature Vault Commit** — Overwriting knowledge vault items without human-in-the-loop checkpoint review.

