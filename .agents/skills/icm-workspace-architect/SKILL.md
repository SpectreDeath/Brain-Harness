---
name: icm-workspace-architect
description: Design, scaffold, audit, and restructure workspaces using Interpretable Context Methodology (ICM, arXiv:2603.16021). Binds folder hierarchy to context scoping (L0-L4), replaces framework code with plain contracts, and validates with the walk test. Do not use for real-time high-concurrency multi-user serving or mid-pipeline dynamic branching.
---

# ICM Workspace Architect

`icm-workspace-architect` is the production architecture engine for designing and restructuring workspaces where the folder structure executes agent orchestration. Rooted in the research of Van Clief & McDermott (*Interpretable Context Methodology: Folder Structure as Agent Architecture*, arXiv:2603.16021), ICM replaces complex multi-agent orchestration frameworks with five-layer context hierarchies, plain markdown contracts, and auditable stage checks.

Every ICM architecture cycle follows a five-stage progression:

```
[1. Scope & Form Selection] ──► [2. Hierarchy & Contracts] ──► [3. Verification Tooling]
                                                                     │
                                                                     ▼
[5. Finalization & Maintenance] ◄── [4. 8-Point Cold Walk Test] ◄────┘
```

See [CARD.md](CARD.md) for the companion summary card, form taxonomy, and invariants checklist.
Consult `/crafting-skills` for craft standards and `/agent-skill-sdlc` for lifecycle validation.

---

## The 10 Mandatory Invariants

1. **One folder, one job** — Each folder performs a single step or holds a single kind of entity, declaring its purpose within itself.
2. **Small, stable entry file** — `AGENTS.md` at root answers "where am I, where does everything live, where do I go for task X" in <60 lines.
3. **Numbering encodes order** — Numbered prefixes (`01_`, `02_`) sequence work where order matters.
4. **Every working folder has a contract** — A `CONTEXT.md` defining Inputs, Process, Outputs, and Check.
5. **Factory vs. product split** — Reference materials (`_shared/`, schemas, voice) live apart from working artifacts (`output/`, records).
6. **Every step ends at a check** — Each stage output must pass a verified check (`check.md` with `pass` or `fail: <why>`) before downstream execution.
7. **Load only what the step needs** — Step context (entry + contract + references + inputs) must stay under ~8,000 tokens.
8. **Plain text, linkable, queryable** — Markdown + YAML frontmatter with relative links that always resolve.
9. **Status lives on disk** — State is reflected directly in filesystem artifacts and generated `_index.md` files.
10. **Instantiate by copying** — New work units are copies of templates from `_templates/`, never blank pages.

---

## 1. Scope & Form Selection

Determine operational mode and select the matching ICM form from the 3 primitives (Sequence, Shelf, Catalog):

1. **Select Operational Mode**:
   - **Build Mode**: Start from an interview or process description. Identify pauses (stage boundaries), invariant rules (factory references), and deliverables.
   - **Restructure Mode**: Take an existing messy folder or repository. Inventory files without moving, classify into 5 roles (`catalog`, `contract`, `factory`, `product`, `dead`), check live referrers, and propose a migration plan.
2. **Select the Form**:
   - **Pipeline**: Sequential production line with handoffs where stage $N$ output is stage $N+1$ input.
   - **Record Library**: Uniform records accumulating status (`_index.md` generated from frontmatter).
   - **Knowledge Bundle**: Linked concepts, claims, and raw sources with verbatim quote checks.
   - **Context Map**: Organizational graph of teams and processes linked by `consumes:` / `produces:`.
   - **System Map**: Codebase audit hierarchy with nouns, verbs, and an impact index.

> **Completion gate**: Mode selected, repeating unit identified, and candidate form confirmed.

---

## 2. Hierarchy & Contract Authoring

Scaffold the five-layer context hierarchy (L0–L4) and author stage contracts:

1. **Scaffold L0 & L1 Catalogs**:
   - Write root `AGENTS.md` (<60 lines) defining identity, routing table, and rules.
   - Author pointers: `CLAUDE.md` (`@AGENTS.md`) and `GEMINI.md` (`@./AGENTS.md`).
   - Author root `CONTEXT.md` mapping the overall pipeline or shelf schema.
2. **Author L2 Stage Contracts**:
   - Every working stage receives a `CONTEXT.md`:
     - `## Inputs`: Backticked exact paths partitioned into `Working (this run)` and `Reference (every run)`.
     - Explicit `Do NOT load:` statement deflecting irrelevant folders.
     - `## Process`: Numbered, deterministic instructions (commands named explicitly).
     - `## Outputs`: Specific file paths in `output/`.
     - `## Check`: Concrete check by person, script, or small model emitting `check.md`.
3. **Scaffold L3 Factory & Templates**:
   - Stable reference material in `_shared/voice.md` or `_meta/schema.md`.
   - Stamp templates in `_templates/`.

> **Completion gate**: L0–L4 hierarchy scaffolded; contracts carry inputs, process, outputs, and checks.

---

## 3. Verification & Guardrail Tooling

Deploy deterministic standard-library verification scripts into the workspace's `_tools/` or execute via Harness CLI:

1. **Link & Input Verification (`icm_links.py`)**:
   - Verify that every markdown link, frontmatter `.md` path, pointer import, and backticked contract input resolves cleanly:
     ```bash
     harness icm links .
     ```
2. **Frontmatter Index Generation (`icm_index.py`)**:
   - Rebuild `_index.md` files across record folders from frontmatter metadata without hand-editing:
     ```bash
     harness icm index records
     ```
3. **Quote & Provenance Verification (`icm_quotes.py`)**:
   - For knowledge bundles, verify verbatim quote matches against `sources/raw/` and enforce `_meta/keep-out.txt`:
     ```bash
     harness icm quotes .
     ```

> **Completion gate**: Verification scripts installed in `_tools/` or CLI verified; zero broken links.

---

## 4. The 8-Point Cold Walk Test

Walk the workspace cold as an agent with zero memory to ensure interpretability:

1. **Where am I**: Can the agent answer its task location within `AGENTS.md` plus at most 2 reads?
2. **Exact Inputs**: Does the active stage contract list exact, verifiable input paths?
3. **Pure Disk Status**: Can system status be determined entirely from disk files and `check.md` verdicts?
4. **No Content in Catalog**: Are routing files (`AGENTS.md`, `CONTEXT.md`) free of content payloads?
5. **Single Source of Truth**: Does each fact live in exactly one home, linked rather than duplicated?
6. **Resolving Links**: Does `harness icm links .` pass with zero broken references?
7. **Token Budget Under 8k**: Does contract + references + inputs remain strictly under 8,000 tokens?
8. **Broken Invariants Explained**: If an invariant is broken on purpose, is the reason documented?

> **Completion gate**: All 8 points of the cold walk test confirmed passing.

---

## 5. Artifact Finalization & Maintenance

Harden and maintain the working ICM workspace:

1. **Audit Compliance**:
   - Run the comprehensive audit command:
     ```bash
     harness icm audit . --json
     ```
   - Assert all 10 mandatory invariants pass with zero error-severity violations.
2. **Continuous Hardening**:
   - Fold stages that no longer require human checks.
   - Script checks that never fail to eliminate manual bottlenecks.
   - Split contracts that grow beyond the 8,000 token ceiling.

> **Completion gate**: Audit passes clean; workspace operational and documented.

---

## The Visual Brief Pillar

Every ICM design or restructuring session must generate an interactive, self-contained HTML visual brief:
1. **Target File Location**: Write to `%TEMP%\\icm-architect-visual-brief-<timestamp>.html` (Windows) or `/tmp/icm-architect-visual-brief-<timestamp>.html` (Unix).
2. **Visual Standards**: Dark theme (`#0d1117`), Tailwind CSS, and Mermaid.js via CDN. Display the 5-layer hierarchy DAG, the 4-axis repository matrix, and the 10 invariants scorecard.
3. **Delivery**: Surface the clickable file path to the user before workspace mutation.

---

## Mandatory Checkpoint Pillar

Prevent premature execution and unreviewed state mutations:
1. Present draft `implementation_plan.md` detailing target form, folder hierarchy, contracts, and migration maps.
2. Set `RequestFeedback: true` in artifact metadata.
3. **STOP and wait** for explicit user review and approval before creating or modifying workspace files.

---

## Anti-Patterns

- **Orchestration Code Sprawl** — Writing complex Python multi-agent orchestration frameworks where simple numbered folders and plain files suffice.
- **Bloated Routing Catalogs** — Stuffing background explanations and domain essays into `AGENTS.md` instead of keeping it strictly under 60 lines.
- **Unchecked Stage Handoffs** — Allowing pipeline execution to proceed without a verified human or automated `check.md` verdict.
- **Context Flooding** — Loading the entire workspace context into agent prompts instead of scoping strictly to the current stage (<8,000 tokens).
- **Hand-Edited Indexes** — Manually maintaining record summaries in `_index.md` instead of generating them deterministically from frontmatter.
- **Blind Restructuring** — Moving or deleting files in an existing codebase without mapping live external referrers first.
- **Duplicated Reference Truths** — Copying style guides or schemas into every stage folder instead of referencing a single home in `_shared/`.
- **Untracked Case Collisions** — Renaming files to `CONTEXT.md` on case-insensitive filesystems without checking for existing `context.md` files.
