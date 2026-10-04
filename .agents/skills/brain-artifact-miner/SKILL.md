---
name: brain-artifact-miner
description: Extract, deconstruct, and synthesize operational skills, plan evolutions, and reusable scratch utilities from IDE brain artifact stores and streaming transcripts. Do not use for simple file listing or raw SQLite database mutations.
---

# Brain Artifact Miner

`brain-artifact-miner` is the filesystem-native workspace archaeology and scratch utility salvage engine for autonomous coding agents. It extracts, deconstructs, and synthesizes operational skills, plan evolutions, and reusable scratch utilities from IDE brain artifact stores (`C:\Users\spectre\.gemini\antigravity-ide\brain\`) and streaming transcripts (`transcript.jsonl` / `transcript_full.jsonl`).

While `conversations/*.db` contains the relational SQLite database of step execution payloads (addressed by [conversation-trajectory-miner](../conversation-trajectory-miner/SKILL.md)), the `brain/` directory constitutes the **filesystem-native epistemic workspace**: an orthogonal artifact tier capturing Python scratch tools, implementation plans, walkthrough documents, subprocess task logs, and untruncated model reasoning streams.

The miner executes an automated 5-stage mining progression across workspace artifact stores:

```
[1. Store Discovery & Boundary-Safe Handshake] → [2. Dual-Transcript & Artifact Topology Index] → [3. Scratch Tool Archaeology & Subprocess Task Triage] → [4. Dual-Lens Cognitive Bifurcation] → [5. Skill SDLC Validation & Knowledge Graph Commit]
```

See [CARD.md](CARD.md) for the companion summary card, prompt catalog, and verification rubrics.
Consult [book-to-skill-forge](../book-to-skill-forge/SKILL.md) for literature-to-skill distillation and [epistemic-memory-lifecycle](../epistemic-memory-lifecycle/SKILL.md) for knowledge item promotion.

---

## 1. Store Discovery & Boundary-Safe Handshake

Enumerate, validate, and establish non-invasive connections to candidate conversation workspaces in the IDE brain store:

```
┌─────────────────────────────────────────────────────────────┐
│             BOUNDARY-RESILIENT HANDSHAKE PROTOCOL           │
├─────────────────────────────────────────────────────────────┤
│ 1. Codec: sys.stdout.reconfigure(encoding='utf-8')          │
│ 2. Safety: Pivot to non-modifying shell reads on denial.    │
│ 3. Paging: Pipe commands with Out-File -Encoding utf8.      │
│ 4. Fallback: Query relational steps when payloads restrict. │
│ 5. Inventory: Enumerate CIDs, mtimes, and artifact trees.   │
└─────────────────────────────────────────────────────────────┘
```

1. **Configure Standard Streams**:
   - Reconfigure standard output and error streams to UTF-8 at module entrypoint to eliminate `cp1252` encoding crashes on Unicode DAG symbols (Rule 23, Rule 50).
2. **Execute Non-Invasive Protection Fallback**:
   - When encountering IDE system protection boundary denials on `brain/<cid>/` paths, pivot immediately to non-modifying shell reads (`Get-Content`, `Get-ChildItem`) or decoupled relational SQLite databases (`conversations/<cid>.db`, Rule 46) without stalling.
3. **Piping & Redirection Hygiene**:
   - Never rely on bare PowerShell `>` redirects for machine-parsed logs; enforce UTF-8 streams via `Out-File -Encoding utf8` or native subprocess piping to prevent UTF-16 LE BOM null-byte corruptions (Rule 26).

Consumes artifact: brain_workspace_directory
Primary artifact: brain_manifest.json

> **Completion criterion**: All target brain directories enumerated via UTF-8-safe shell reads, codec invariants initialized, zero protection boundary stalls, and zero bare > PowerShell redirects in any log-producing command.

---

## 2. Dual-Transcript & Artifact Topology Index

Extract and cross-link execution streams and strategic documents across gigabyte-scale session trees without memory exhaustion:

1. **Construct Binary Byte-Offset Seek Table**:
   - For multi-megabyte `transcript.jsonl` and `transcript_full.jsonl` files exceeding 10 MB, never load files line-by-line via `f.readlines()` (Rule 48).
   - Scan the file once in binary mode (`open(..., 'rb')`) to build an in-memory lookup table mapping `step_index` to `(byte_offset, byte_length)`.
   - Execute all subsequent step retrievals via direct $O(1)$ random seeks (`f.seek(offset)`, `f.read(length)`).
2. **Dual-Transcript Synchronization & Truncation Dereference**:
   - Map compact `transcript.jsonl` steps to their untruncated reasoning counterparts in `transcript_full.jsonl` using `step_index` as the join key (Rule 22).
   - When `is_truncated: true` is detected in a compact step, automatically dereference to `transcript_full.jsonl` to recover planner thoughts and raw tool arguments.
3. **Artifact Lifecycle Versioning & Null-Safe Metadata Parsing**:
   - Index `implementation_plan.md`, `walkthrough.md`, and `task.md` documents using bounded directory traversal (depth $\le 3$, Rule 52).
   - When parsing `.metadata.json` sidecar files, extract optional collections via `dict.get("key") or []` to guard against explicit JSON `null` values returning `None` (Rule 33).
   - Compare initial plans against final walkthroughs to measure scope deltas and completion drift.

Consumes artifact: brain_manifest.json
Primary artifact: artifact_topology_map.json

> **Completion criterion**: O(1) byte-offset index built for all transcripts >10 MB; dual-transcript step cross-links established with is_truncated dereference logic; artifact lifecycle map constructed with null-safe sidecar parsing.

---

## 3. Scratch Tool Archaeology & Subprocess Task Triage

Catalog reusable domain utilities from ephemeral scratch folders and triage background process execution health:

```
| Category | File Archetype | Primary Role | Inspection Method |
| :--- | :--- | :--- | :--- |
| ast_and_lint | lint_*.py, check_*.py | Structural syntax verification | ast.parse & ast.walk |
| database_and_sql | db_*.py, query_*.py | Relational schema reflection | sqlite3 PRAGMA reflection |
| brief_and_visual | brief_*.py, visual_*.py | Standalone HTML generation | Regex doubled-brace checks |
| test_and_verify | test_*.py, verify_*.py | Characterization test contracts | pytest invocation patterns |
| search_and_grep | search_*.py, grep_*.py | Bounded pattern extraction | Regex token analysis |
| task_subprocesses | task-*.log | Subprocess exit triage | Stderr ring-buffer scan |
```

1. **AST-Based Scratch Tool Classification**:
   - Scan dormant Python scripts in `brain/<cid>/scratch/` using bounded directory walks (depth $\le 3$, Rule 52).
   - Parse scripts via `ast.parse` and `ast.walk` to inspect functions, docstrings, and imports (Rule 42). Classify scripts into typed domain categories.
2. **Defensive Batch Exception Logging**:
   - Never use bare `except Exception: continue` in batch scanning loops (Rule 32).
   - Log unexpected errors at `logger.warning()`, and explicitly reraise programming errors (`NameError`, `TypeError`, `AttributeError`) so schema and import defects fail loudly.
3. **Subprocess Stderr Drainage & Deadlock Triage**:
   - Ingest `.system_generated/tasks/task-*.log` background task outputs.
   - Scan for non-zero exit codes, tracebacks, and proactor pipe buffer deadlocks.
   - Maintain a bounded ring-buffer for stderr lines to surface failure diagnostics cleanly (Rule 53).
4. **F-String Template Hygiene**:
   - When synthesizing HTML visual briefs, ensure all CSS rules and regex syntax inside Python f-strings use doubled braces (`{{`, `}}`) to prevent runtime string formatting crashes (Rule 51).

Consumes artifact: artifact_topology_map.json
Primary artifact: scratch_and_task_catalog.json

> **Completion criterion**: >= 50 scripts classified across >= 4 categories; background task triage report emitted with non-zero exit code and deadlock signature counts; zero silent except: continue suppressions; zero bare > PowerShell redirects in log capture commands.

---

## 4. Dual-Lens Cognitive Bifurcation (Epistemic & Procedural)

Strictly bifurcate distilled artifact learnings into two complementary operational seams (Rule 41):

Consumes artifact: scratch_and_task_catalog.json
Primary artifact: epistemic_procedural_spec.json

> **Completion criterion**: Distillation strictly bifurcated into validated Knowledge Vault items with unbroken isnad lineage and executable skill scaffolds with zero-fork configuration.

### 4a. Epistemic Introspection Seam (Knowledge Vault)
- Extract verified heuristics, workspace topologies, and failure recovery invariants from artifact lifecycle drift and background task triage.
- Commit distilled items to the Knowledge Vault under `.harness/knowledge/<ki_id>/` strictly adhering to the canonical dual-file directory format (`metadata.json` + `summary.md`, Rule 40).
- Anchor every claim with unbroken isnad provenance citing primary conversation UUIDs, script paths, and transcript step indices.

### 4b. Procedural Skill Synthesis Seam (Agent Skill Scaffolding)
- Synthesize executable agent skills under `.agents/skills/<skill-name>/` with structured 5-stage progression matrices.
- Author companion summary cards (`CARD.md`) with ASCII metadata boxes, stage tables, and mandatory invariant checklists using relative links (Rule 37, Rule 47).
- Provide co-located `config.default.yaml` defining baseline operational budgets (timeouts, token limits, retry bounds, Rule 44).
- Implement modular, executable Python scripts in `scripts/` using domain-prefixed names (`brain_artifact_miner.py`) to prevent global `sys.modules` collisions (Rule 57).

---

## 5. Skill SDLC Validation & Knowledge Graph Commit

Validate the synthesized artifacts against craft standards and index the capabilities into the runtime knowledge graph:

1. **Execute Diagnostic Craft Validation**:
   - Run `SkillValidator.validate()` to assert complete compliance across structural, frontmatter, pillar, and card rules (Rule 34).
   - Evaluate boolean status via `report.valid` and inspect granular rule executions through `report.checks` (never check `.passed`).
   - Verify frontmatter description length (100–350 characters) with explicit negative boundaries (Rule 44).
   - Ensure companion `CARD.md` utilizes single-pipe `│` borders and the exact `SKILL: <name>` tag (Rule 37).
2. **Index into Skill Knowledge Graph**:
   - Trigger `BuiltinSkillRegistryService.index_catalog()` to register the new skill node and compute topological dependency edges (`FEEDS`, `REQUIRES`, Rule 35, Rule 55).
3. **Register in Context Map**:
   - Update `CONTEXT-MAP.md` under the Agent Orchestration domain, defining explicit negative boundaries distinguishing from relational trajectory mining.

Consumes artifact: epistemic_procedural_spec.json
Primary artifact: skill_validation_report.json

> **Completion criterion**: Skill SDLC pipeline completes with valid status and zero warnings; skill indexed in knowledge graph with validated FEEDS edges.

---

## The Three Foundational Pillars

### Pillar I: The Visual Brief
Synthesize findings, artifact inventory heatmaps, and task log triage metrics into a self-contained HTML visual brief written to `%TEMP%\brain-artifact-miner-<timestamp>.html` (or `/tmp/brain-artifact-miner-<timestamp>.html` on Unix) loading Tailwind CSS and Mermaid.js via CDN. Present the absolute clickable path to the user for visual review.

### Pillar II: The Mandatory Checkpoint
When proposing new skill creation, structural modifications, or epistemic knowledge commits, always author an `implementation_plan.md` artifact with `RequestFeedback: true`. The agent must **STOP and wait** for explicit human confirmation before executing mutating actions.

### Pillar III: Explicit Anti-Patterns
Rigid behavioral boundaries must be maintained to prevent catastrophic failure modes.

---

## Anti-Patterns

- **Unbounded Directory Traversal** — Executing unpruned recursive walks across 343 conversation directories causing pipe exhaustion and CPU thrash instead of depth-bounded traversal.
- **Protection Boundary Stall** — Halting or repeatedly failing when file tools encounter IDE system protection denials instead of pivoting immediately to non-modifying shell reads.
- **Scratch Script Amnesia** — Leaving valuable AST tools and diagnostic scripts dormant in dead conversation folders without cataloging or salvage.
- **Silent Batch Exception Suppression** — Using bare `except Exception: continue` in batch scanning loops, masking missing imports and schema bugs as empty classification results.
- **Subprocess Pipe Deadlock Blindness** — Ignoring background task stderr dumps and buffer locks in task logs instead of ring-buffered stderr drainage.
- **Truncated Transcript Blindness** — Relying solely on compact transcripts where model thoughts are truncated without auto-dereferencing to full transcripts.
- **Generic Script Module Naming** — Naming helper scripts with generic names like `miner.py` that pollute `sys.modules` instead of domain-prefixed naming.
- **Absolute URI Links in CARD.md** — Using `file:///` absolute paths in cross-skill references breaking portability across CI runners and container sandboxes.
- **JSON Null-Field Iteration Crash** — Using `dict.get("key", [])` when reading optional sidecar lists, crashing on explicit JSON `null` values instead of `dict.get("key") or []`.
- **Epistemic Seam Bypass** — Scaffolding procedural skill files while failing to commit ground-truth isnad items to the Knowledge Vault.
- **Unverified Skill Scaffolding** — Committing skills without running `SkillValidator` or consuming reports via `report.valid` and `report.checks`.
