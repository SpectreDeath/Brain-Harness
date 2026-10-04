---
name: temp-artifact-miner
description: Extract, triage, and synthesize architecture decision records, visual DAG briefs, and ephemeral test diagnostics from system temporary directories and pytest sandboxes. Do not use for relational SQLite queries, persistent brain workspaces, or destructive temp purging.
---

# Temp Artifact Miner

`temp-artifact-miner` is the ephemeral runtime archaeology and visual architecture salvage engine for autonomous coding agents. It extracts, triages, and synthesizes architecture decision records, visual DAG briefs, and test diagnostics from system temporary stores (`%TEMP%` / `C:\Users\spectre\AppData\Local\Temp\`) and ephemeral pytest sandbox environments (`pytest-of-spectre/`).

While `conversations/*.db` contains relational execution step records (addressed by [conversation-trajectory-miner](../conversation-trajectory-miner/SKILL.md)) and `brain/<cid>/` contains persistent workspace scratch scripts and plans (addressed by [brain-artifact-miner](../brain-artifact-miner/SKILL.md)), the temporary directory hosts the **ephemeral visual and runtime deliverables**: interactive HTML briefs mandated by Pillar I of the deep-module craft standards (Mermaid workflows, diagnostic scorecards, topology graphs), alongside temporary pytest sandbox test environments.

Because `%TEMP%` is subject to periodic operating system purges and restart wipes, high-value visual architecture briefs and sandbox mock fixtures risk permanent loss unless an agent can proactively discover, inventory, parse, and salvage them into permanent repository documentation (`docs/`) or the Knowledge Vault (`.harness/knowledge/`).

The miner executes an automated 5-stage mining progression across ephemeral runtime stores:

```
[1. Ephemeral Store Discovery & Census Handshake] → [2. Visual Brief & Topology Parsing] → [3. Test Sandbox & Diagnostics Triage] → [4. Dual-Lens Cognitive Bifurcation] → [5. Skill SDLC Validation & Knowledge Graph Commit]
```

See [CARD.md](CARD.md) for the companion summary card, prompt catalog, and verification rubrics.
Consult [book-to-skill-forge](../book-to-skill-forge/SKILL.md) for literature-to-skill distillation and [epistemic-memory-lifecycle](../epistemic-memory-lifecycle/SKILL.md) for knowledge item promotion.

---

## 1. Ephemeral Store Discovery & Census Handshake

Enumerate, validate, and establish non-modifying connections to candidate visual briefs, reports, and sandbox environments in `%TEMP%`:

```
┌─────────────────────────────────────────────────────────────┐
│             NON-MODIFYING EPHEMERAL DISCOVERY PROTOCOL      │
├─────────────────────────────────────────────────────────────┤
│ 1. Codec: sys.stdout.reconfigure(encoding='utf-8')          │
│ 2. Safety: Strictly read-only; never delete files in %TEMP%.│
│ 3. Resilience: Gracefully tolerate disappearing temp files. │
│ 4. Paging: Pipe commands with Out-File -Encoding utf8.      │
│ 5. Inventory: Enumerate HTML briefs, sizes, and mtimes.     │
└─────────────────────────────────────────────────────────────┘
```

1. **Configure Standard Streams**:
   - Reconfigure standard output and error streams to UTF-8 at module entrypoint to eliminate `cp1252` encoding crashes on Unicode DAG symbols (Rule 23, Rule 50).
2. **Execute Non-Modifying Ephemeral Reads**:
   - The miner is strictly read-only. Never execute destructive deletion commands (`Remove-Item`, `rm -rf`) across `%TEMP%`. Active proactor IPC pipes, live test runs, and un-salvaged briefs must never be disrupted (Rule 46).
3. **Handle Ephemeral Volatility Defensively**:
   - Batch discovery loops must anticipate race conditions with external processes or OS cleanup. Wrap file reads in defensive handlers that log unexpected errors at `logger.warning()` and reraise programming errors (`NameError`, `TypeError`, `AttributeError`, Rule 32).
4. **Piping & Redirection Hygiene**:
   - Never rely on bare PowerShell `>` redirects for machine-parsed logs; enforce UTF-8 streams via `Out-File -Encoding utf8` or native subprocess piping to prevent UTF-16 LE BOM null-byte corruptions (Rule 26).

Consumes artifact: temp_directory
Primary artifact: temp_manifest.json

> **Completion criterion**: All candidate visual briefs, reports, and sandbox directories in `%TEMP%` enumerated via non-blocking, non-destructive reads; codec invariants initialized; and manifest emitted without file locks.

---

## 2. Visual Brief & Topology Parsing

Extract structured decision logic, Mermaid DAG workflows, and diagnostic scorecards from ephemeral HTML files without context flooding:

1. **Multi-Pass Structured HTML Extraction**:
   - Apply a multi-pass regex and DOM boundary parsing pipeline to isolate embedded `<div class="mermaid">` or `<pre class="mermaid">` flowcharts, Diagnostic Scorecard Tables (`<table>`), and Anti-Pattern Defense Matrices (Rule 42, Rule 51).
   - Extract title, subtitle, empirical census metrics, and generating skill signatures.
2. **Context Window Economy & Heavy Topology Bounding**:
   - Ephemeral snapshots generated by skill graph introspection tools (e.g. `skill-graph-*.html`) contain full interactive Cytoscape or SVG DOM graphs exceeding 400 KB each.
   - The parser must detect payloads exceeding the configured size threshold (default: 100 KB) and synthesize high-density topological summaries (node count, edge count, cluster density) rather than flooding the LLM context window with raw DOM blobs (Rule 9, Rule 48).
3. **Artifact Attribution & Isnād Tracking**:
   - Compute the SHA-256 checksum, last modification timestamp, and source path for each extracted brief to support cryptographically grounded provenance verification (Rule 40).

Consumes artifact: temp_manifest.json
Primary artifact: brief_catalog.json

> **Completion criterion**: Structured brief catalog compiled; Mermaid DAGs and evaluation scorecards extracted intact; heavy topology graphs bounded; and zero raw Cytoscape DOM bloat injected into context.

---

## 3. Test Sandbox & Diagnostics Triage

Inspect ephemeral subprocess test environments and diagnostic logs to extract failure patterns and isolated mock architectures:

1. **Bounded Traversal of Pytest Sandboxes**:
   - Inspect temporary pytest directories (`pytest-of-spectre/pytest-*`) using strictly bounded directory traversal (depth $\le 3$, Rule 52).
   - Actively prune noise directories (`.git`, `.venv`, `node_modules`, `__pycache__`) to prevent CPU spin and proactor pipe exhaustion.
2. **Mock Fixture Topology Archaeology**:
   - Inspect temporary mock skill directories generated during test runs (e.g. `test_corpus_idf_routing0`, `test_feeds_edge_acyclicity0`) via AST parsing to catalog synthesized test topologies and contract edge definitions.
3. **Bounded Ring-Buffer Stderr Diagnostics**:
   - When triaging crash logs (`cv_debug.log`, `mat-debug-*.log`, `LEG10N-*.log`), stream trailing lines into a bounded ring buffer (`deque(maxlen=50)`) to isolate root-cause stack traces without loading multi-megabyte log files into memory (Rule 53).

Consumes artifact: temp_manifest.json
Primary artifact: sandbox_triage_report.json

> **Completion criterion**: Pytest sandbox fixtures triaged to bounded depth; noise roots pruned; trailing diagnostic stderr lines isolated; and zero untrusted test script executions.

---

## 4. Dual-Lens Cognitive Bifurcation

Per **Rule 41 (Dual-Lens Cognitive Distillation)**, strictly bifurcate salvaged ephemeral intelligence into two distinct architectural seams:

```
┌─────────────────────────────────────────────────────────────┐
│             DUAL-LENS COGNITIVE BIFURCATION SEAM            │
├──────────────────────────────┬──────────────────────────────┤
│ 1. Epistemic Seam            │ 2. Procedural Seam           │
│ - Knowledge Vault retention  │ - Reusable agent tooling     │
│ - Canonical dual-file format │ - Salvaged repo documentation│
│ - Verified isnad claim trace │ - Diagnostic scorecard rules │
└──────────────────────────────┴──────────────────────────────┘
```

1. **Epistemic Seam (Knowledge Vault Retention)**:
   - Extract enduring architectural breakthroughs, design heuristics, and tri-store relationship models.
   - Commit to `.harness/knowledge/<ki_id>/` using the canonical dual-file directory format (`metadata.json` + `summary.md`, Rule 40).
   - Declare explicit isnād claim chains with verified status referencing source brief timestamps and sha256 hashes.
2. **Procedural Seam (Skill & Documentation Salvage)**:
   - Identify visual architecture reviews that represent approved system designs and export them into permanent repository documentation (`docs/architecture/`).
   - Scaffolding executable helper tools and automated cron jobs to periodically archive ephemeral briefs before OS purges.

Consumes artifact: brief_catalog.json
Primary artifact: epistemic_procedural_spec.json

> **Completion criterion**: Cognitive outputs strictly separated into a verified dual-file Knowledge Vault item and persistent documentation or procedural code.

---

## 5. Skill SDLC Validation & Knowledge Graph Commit

Validate the synthesized capabilities and register the new intelligence node in the active workspace ecosystem:

1. **Execute Diagnostic Craft Validation**:
   - Assert that YAML frontmatter length is bounded between 100 and 350 characters with action verbs and explicit negative boundaries (Rule 44).
   - Assert single-pipe `│` borders in `CARD.md` with exact `SKILL: temp-artifact-miner` header tag and `- [ ]` checklist rules (Rule 37).
   - Assert `## Anti-Patterns` heading with `- **Name** — Description` formatting (Rule 37).
   - Assert relative links across all documents (Rule 47).
2. **Index into Skill Knowledge Graph**:
   - Run `harness skills graph` to register the `temp-artifact-miner` node and map `FEEDS` relationships to `book-to-skill-forge` and `epistemic-memory-lifecycle`.
3. **Register in Context Map**:
   - Add the skill under **1. Agent Orchestration** in `CONTEXT-MAP.md` with explicit negative boundaries.

Consumes artifact: epistemic_procedural_spec.json
Primary artifact: skill_validation_report.json

> **Completion criterion**: `SkillValidator` passes with `report.valid == True` and zero warnings; knowledge graph indexed; and context map updated.

---

## The Three Core Pillars

### Pillar I: The Visual Brief (%TEMP%)
The miner operates with the core understanding that `%TEMP%` hosts high-value visual deliverables. Synthesize findings, artifact inventory heatmaps, and brief triage metrics into an interactive HTML visual brief written to `%TEMP%\temp-artifact-miner-<timestamp>.html` loading Tailwind CSS and Mermaid.js via CDN. Present the absolute clickable path to the user for visual review.

### Pillar II: The Mandatory Checkpoint (RequestFeedback: true)
When proposing new skill creation, structural modifications, or epistemic knowledge commits, always author an `implementation_plan.md` artifact with `RequestFeedback: true`. The agent must **STOP and wait** for explicit human confirmation before executing mutating actions.

### Pillar III: Explicit Anti-Patterns & Defenses
Rigid behavioral boundaries and negative constraints must be maintained to prevent catastrophic failure modes such as destructive temp deletions or context window flooding from heavy topologies (Rule 9, Rule 48).

---

## Anti-Patterns

- **Ephemeral Purge Amnesia** — Treating `%TEMP%` as disposable junk and losing high-value visual briefs, Mermaid diagrams, and decision scorecards.
- **Destructive Temp Wiping** — Running blind `Remove-Item` or `rm -rf` across Temp, killing live proactor IPC pipes, breaking active test runs, or wiping unsaved briefs.
- **Topology Context Flooding** — Dumping raw 400KB+ Cytoscape or SVG interactive graphs directly into agent context windows, causing context blowout.
- **Unbounded Sandbox Traversal** — Recursively traversing deep pytest sandbox trees into virtualenvs or node_modules without pruning, triggering proactor timeouts.
- **Bare PowerShell Redirection** — Using bare `>` to write temporary logs, producing UTF-16 LE corruptions.
- **Unverified Isnād Attribution** — Salvaging architectural decisions into knowledge items without tracking source brief mtime, file path, and generating skill.
