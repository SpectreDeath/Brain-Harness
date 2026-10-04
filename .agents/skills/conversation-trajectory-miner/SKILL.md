---
name: conversation-trajectory-miner
description: Extract, deconstruct, and synthesize operational skills, debugging rubrics, and regression invariants from IDE conversation databases and execution trajectories. Do not use for superficial keyword search or live streaming logs.
---

# Conversation Trajectory Miner

`conversation-trajectory-miner` is the autobiographical archaeology and knowledge distillation engine for autonomous coding agents. It extracts, deconstructs, and synthesizes operational skills, debugging rubrics, and regression invariants from IDE conversation databases (`conversations/*.db`) and runtime execution trajectories (`brain/<cid>/transcript.jsonl`).

Rather than relying on human prompt intuition or superficial keyword searches, this engine executes an automated 5-stage mining progression across multi-store session histories:

```
[1. Store Handshake & Relational Autopsy] → [2. Byte-Offset Seam Unpacking & Lazy Indexing] → [3. Friction Archaeology & Step-Type Frequency Analysis] → [4. Dual-Lens Cognitive Bifurcation] → [5. Skill SDLC Validation & Knowledge Graph Commit]
```

See [CARD.md](CARD.md) for the companion summary card, prompt catalog, and verification rubrics.
Consult `/book-to-skill-forge` for literature distillation and `/epistemic-memory-lifecycle` for knowledge item promotion.

---

## 1. Store Handshake & Relational Autopsy

Establish proactor-safe, read-only connections to target conversation stores and catalog active trajectory metadata:

```
┌─────────────────────────────────────────────────────────────┐
│                 READ-ONLY HANDSHAKE PROTOCOL                │
├─────────────────────────────────────────────────────────────┤
│ 1. Connect: sqlite3.connect("file:<path>?mode=ro", uri=True)│
│ 2. Safety: Never lock live WAL proactors during mining.     │
│ 3. Schema: Map trajectory_meta, steps, executor_metadata.   │
│ 4. Fallback: Query relational steps when payloads restrict. │
│ 5. Manifest: Inventory CIDs, step counts, and disk bytes.   │
└─────────────────────────────────────────────────────────────┘
```

1. **Execute Proactor-Safe Handshake**:
   - Always open conversation databases using SQLite read-only URI mode (`file:{path}?mode=ro`, Rule 22). Live IDE proactors maintain concurrent WAL locks; opening databases in standard read-write mode risks lock contention and database corruption.
2. **Catalog Relational Schema**:
   - Inspect table topologies across `trajectory_meta`, `steps`, `gen_metadata`, `executor_metadata`, `parent_references`, and `battle_mode_infos`.
3. **Execute Non-Invasive Protection Fallback**:
   - When encountering system protection boundaries on `brain/<cid>/` artifact directories, immediately fall back to the decoupled relational conversation database (`conversations/<cid>.db`, Rule 46) to retrieve execution step history.

Consumes artifact: conversation_directory
Primary artifact: trajectory_manifest.json

> **Completion criterion**: Proactor-safe read-only connection established across target conversation databases without file lock contention; schema verified and trajectory manifest generated.

---

## 2. Byte-Offset Seam Unpacking & Lazy Indexing

Extract and index sequential execution records from gigabyte-scale logs without memory exhaustion:

1. **Construct Binary Byte-Offset Seek Table**:
   - For multi-megabyte `transcript.jsonl` files or batch conversation exports, never load files line-by-line via `f.readlines()` (Rule 48).
   - Scan the file once in binary mode (`open(..., 'rb')`) to build an in-memory lookup table mapping step indices to `(byte_offset, byte_length)`.
   - Execute all subsequent step retrievals via direct $O(1)$ random seeks (`f.seek(offset)`, `f.read(length)`).
2. **Lossy Protobuf Seam Decoding**:
   - When extracting user intent from binary protobuf columns (`steps.step_payload`), apply lossy UTF-8 decoding (`errors='ignore'`) coupled with printable ASCII regex filters to isolate user prompts and tool payloads without crashing on unrecognized protobuf wire formats.

Consumes artifact: trajectory_manifest.json
Primary artifact: byte_offset_index.json

> **Completion criterion**: Binary byte-offset index table compiled for all transcript files; sub-millisecond seek retrieval verified without full-corpus memory loading.

---

## 3. Friction Archaeology & Step-Type Frequency Analysis

Quantify trajectory health, identify failure clusters, and isolate hard-won debugging breakthroughs:

```
| Step Type | Semantic Role | Friction Indicator | Diagnostic Metric |
| :--- | :--- | :--- | :--- |
| USER_INPUT | Problem Formulation | Repetitive Clarifications | Task ambiguity rate |
| PLANNER_RESPONSE | Autonomous Reasoning | Long-running loop count | Planning convergence |
| TOOL_EXECUTION | Action Execution | Repeated command retries | Tool execution friction |
| ERROR | Boundary Failure | Non-zero exit codes / exceptions | Defect density |
```

1. **Quantify Step-Type Distributions**:
   - Calculate step-type ratios across sessions (`PLANNER_RESPONSE`, `TOOL_EXECUTION`, `USER_INPUT`, `ERROR`).
2. **Detect Retry Loops & Error Cascades**:
   - Identify consecutive failure clusters where tool executions repeatedly failed and self-repaired.
   - Extract the specific error messages and the subsequent successful diff that resolved the blocker.
3. **Isolate Hard-Won Invariants**:
   - Translate resolved friction points into architectural invariants, guarding against recurring regressions.

Consumes artifact: byte_offset_index.json
Primary artifact: friction_diagnostic_report.json

> **Completion criterion**: Step-type distribution quantified; retry loops and error hotspots isolated into a prioritized friction scorecard.

---

## 4. Dual-Lens Cognitive Bifurcation (Epistemic & Procedural)

Strictly bifurcate distilled trajectory learnings into two complementary operational seams (Rule 41):

Consumes artifact: friction_diagnostic_report.json
Primary artifact: epistemic_procedural_spec.json

> **Completion criterion**: Distillation strictly bifurcated into validated Knowledge Vault items with unbroken isnad lineage and executable skill scaffolds with zero-fork configuration.

### 4a. Epistemic Introspection Seam (Knowledge Vault)
- Extract foundational mental models, architecture trade-offs, and proven invariants.
- Commit distilled items to the Knowledge Vault under `.harness/knowledge/<ki_id>/` strictly adhering to the canonical dual-file directory format (`metadata.json` + `summary.md`, Rule 40).
- Anchor every claim with unbroken isnad provenance citing primary source code files and verification tests.

### 4b. Procedural Skill Synthesis Seam (Agent Skill Scaffolding)
- Synthesize executable agent skills under `.agents/skills/<skill-name>/` with structured 5-stage progression matrices.
- Author companion summary cards (`CARD.md`) with ASCII metadata boxes, stage tables, and mandatory invariant checklists (Rule 37).
- Provide co-located `config.default.yaml` defining baseline operational budgets (timeouts, token limits, retry bounds, Rule 44).
- Implement modular, executable Python scripts in `scripts/` with UTF-8 stream reconfigurations (Rule 23, Rule 50).

---

## 5. Skill SDLC Validation & Knowledge Graph Commit

Validate the synthesized artifacts against craft standards and index the capabilities into the runtime knowledge graph:

1. **Execute Diagnostic Craft Validation**:
   - Run `SkillValidator.validate()` to assert complete compliance across structural, frontmatter, pillar, and card rules (Rule 34).
   - Verify frontmatter description length (100–350 characters) with explicit negative boundaries (Rule 44).
   - Ensure companion `CARD.md` utilizes single-pipe `│` borders and the exact `SKILL: <name>` tag (Rule 37).
2. **Index into Skill Knowledge Graph**:
   - Trigger `BuiltinSkillRegistryService.index_catalog()` to register the new skill node and compute topological dependency edges (`FEEDS`, `REQUIRES`, Rule 35, Rule 55).
3. **Register in Context Map**:
   - Update `CONTEXT-MAP.md` under the Agent Orchestration domain, defining explicit negative boundaries.

Consumes artifact: epistemic_procedural_spec.json
Primary artifact: skill_validation_report.json

> **Completion criterion**: Skill SDLC pipeline completes with valid status and zero warnings; skill indexed in knowledge graph with validated FEEDS edges.

---

## The Three Foundational Pillars

### 1. The Visual Brief
Synthesize findings, trajectory heatmaps, and friction metrics into a self-contained HTML visual brief written to `%TEMP%\conversation-trajectory-miner-<timestamp>.html` (or `/tmp/conversation-trajectory-miner-<timestamp>.html` on Unix) loading Tailwind CSS and Mermaid.js via CDN. Present the absolute clickable path to the user for visual review.

### 2. The Mandatory Checkpoint
When proposing new skill creation, structural modifications, or epistemic knowledge commits, always author an `implementation_plan.md` artifact with `RequestFeedback: true`. The agent must **STOP and wait** for explicit human confirmation before executing mutating actions.

### 3. Explicit Anti-Patterns
Rigid behavioral boundaries must be maintained to prevent catastrophic failure modes.

---

## Anti-Patterns

- **Unbounded String Scanning** — Loading massive SQLite blobs or multi-megabyte JSONL transcripts entirely into memory with `f.readlines()` or sequential string scans instead of binary byte-offset indexing.
- **Lock Contention Crash** — Opening active SQLite WAL databases without `?mode=ro` URI mode, causing disk lock contention or database corruption with live IDE worker proactors.
- **Single-Lens Monolith** — Forgetting to bifurcate mining outputs into both epistemic ground-truth (Knowledge Vault) and procedural execution (executable skills).
- **Protobuf Deserialization Panic** — Crashing when encountering binary protobuf payloads in `step_payload` instead of falling back to UTF-8 lossy decoding and `executor_metadata` relational tables.
- **Polite Rubber-Stamping** — Generating flattering conversational summaries instead of extracting concrete failure modes, error patterns, and regression invariants.
- **Shotgun Knowledge Commits** — Writing raw, unvalidated JSON dumps directly into the root knowledge folder instead of canonical dual-file directories (`metadata.json` + `summary.md`).
- **Unbounded Directory Walking** — Recursively traversing entire IDE brain directories without pruning noise roots (`.git`, `.venv`, cache) or enforcing scan depth limits.
