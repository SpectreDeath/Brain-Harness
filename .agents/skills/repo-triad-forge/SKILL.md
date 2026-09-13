---
name: repo-triad-forge
description: Orchestrate the end-to-end repository triad pipeline: 5-stage cognitive audit, dual-file Knowledge Vault commits, slotted skill synthesis, and sandboxed Harness plugin forging with bounded self-repair. Do not use for superficial repo browsing or trivial single-file edits.
---

# Repo-Triad Forge: Unified Ingestion, Audit, Skill & Plugin Pipeline

`repo-triad-forge` is the master meta-orchestrator that ingests an external repository and coordinates the unified cognitive triad:
1. **Multi-Axis Cognitive Audit** ([`deep-repo-auditor`](../deep-repo-auditor/SKILL.md))
2. **Deep Skill Synthesis & Domain Modeling** ([`deep-skill-forge`](../deep-skill-forge/SKILL.md))
3. **Sandboxed Plugin Forging** ([`repo-to-plugin-forge`](../repo-to-plugin-forge/SKILL.md))
4. **Epistemic Knowledge Item Retention** ([`epistemic-memory-lifecycle`](../epistemic-memory-lifecycle/SKILL.md))

See [CARD.md](CARD.md) for the companion summary card, stage progression table, and invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline operational budgets and timeout thresholds.

---

## The 5-Stage Triad Pipeline Progression

```
[1. Pre-Flight Inspection & 5D Compute Assessment]
                       │
                       ▼
[2. Multi-Axis Cognitive Audit & Interactive Visual Briefs (%TEMP%)]
                       │
                       ▼
[3. Interactive Knowledge Vault Checkpoint (ask_question)]
  └── Commit Canonical Dual-File KIs (.harness/knowledge/<id>/)
                       │
                       ▼
[4. Deep Skill & Sandboxed Plugin Scaffolding]
  ├── Skill (.agents/skills/<name>/) with slotted domain models & test contract
  ├── ServiceKey & Protocol (src/harness/services/)
  └── Plugin (plugins/<category>/<name>/) with PluginValidator compliance
                       │
                       ▼
[5. Verification Suite, Bounded Self-Repair & Ecosystem Registration]
  ├── Test Suite Execution (pytest with Rule 30/Rule 43)
  ├── Multi-Layer Context Linting (python -m harness.commands.context lint)
  └── Skill Knowledge Graph Indexing (harness skills graph)
```

---

## 1. Pre-Flight Inspection & 5D Compute Assessment

Inspect the target repository's high-level topology and evaluate reasoning tier calibration:

1. **Introspect Repository Structure**:
   - Run `triad_pipeline.py inspect --repo <path>` to scan language manifests (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`).
   - Identify monorepo packages, blast-radius root files, and git history continuity.
   - If the repository is outside the active workspace directory, immediately fall back to non-modifying shell extraction to respect permission boundaries (Rule 46).
2. **Calibrate 5D Compute Complexity**:
   - Assess Span, Depth, Concurrency, Rigor, and Heterogeneity.
   - If composite complexity $\ge 0.75$, automatically lock model reasoning budgets to High and subprocess timeouts to 300s+ (Rule 25).

> **Completion criterion**: Structural inspection complete, monorepo packages mapped, and compute tier calibrated.

---

## 2. Multi-Axis Cognitive Audit & Interactive Visual Briefs

Execute deep codebase introspection and generate user-facing visual transparency:

1. **Execute 5-Stage Audit**:
   - Run Stage 1 (Compute Assessment), Stage 2 (Causal DAG Data Topology), Stage 3 (AST Archaeology & Commit Trajectory), Stage 4 (Deep Skill Scoping), and Stage 5 (Plugin Architecture Design).
2. **Generate 5 Dark-Mode Interactive Visual Briefs**:
   - Compile self-contained HTML visual briefs into `%TEMP%` (Compute Assessor, Data Topology, Repo Reader, Deep-Skill Forge, and Repo-to-Plugin Forge).
   - Display Mermaid architecture diagrams, data-flow DAGs, and scorecards.
   - Surface clickable file URLs directly to the user.

> **Completion criterion**: All 5 HTML visual briefs rendered to `%TEMP%` and linked in conversation.

---

## 3. Interactive Knowledge Vault Checkpoint

Enforce human-in-the-loop governance before committing persistent memory:

1. **Formulate Epistemic Isnad Claims**:
   - Isolate 3 to 5 high-leverage architectural breakthroughs, invariants, or domain patterns.
   - Attach timestamped lineage nodes with exact source file and line coordinates (`file#L1-L80`).
2. **Present Multi-Select Checkpoint Modal**:
   - Trigger `ask_question` with `is_multi_select: true` presenting candidate Knowledge Items.
3. **Commit Canonical Dual-File Directories (Rule 40)**:
   - For all user-approved items, write dual files to `.harness/knowledge/<ki_id>/`:
     - `metadata.json`: Machine-readable isnad claims, sha256 hashes, status, and tags.
     - `summary.md`: Epistemic introspection, mental models, decision heuristics, and anti-pattern defenses.

> **Completion criterion**: Interactive checkpoint approved and dual-file KIs persisted to `.harness/knowledge/`.

---

## 4. Deep Skill & Sandboxed Plugin Scaffolding

Scaffold production-grade agent capabilities and sandboxed micro-kernel plugins:

1. **Forge Production Skill (`.agents/skills/<name>/`)**:
   - `SKILL.md`: Frontmatter bounded between 100 and 350 characters (Rule 44), 3 foundational pillars, and structured `## Anti-Patterns` (Rule 37).
   - `CARD.md`: Standard single-pipe `│` borders, `SKILL: <name>` header tag, and blocking invariants.
   - `config.default.yaml`: Baseline operational budgets (Rule 44).
   - `scripts/`: Domain engine implementing slotted/frozen dataclass entities (`slots=True, frozen=True`, Rule 12).
   - `tests/`: Contract test suite validating immutability using direct attribute assignment (Rule 43).
2. **Elevate Micro-Kernel Service Protocol (`src/harness/services/`)**:
   - Define typed `@runtime_checkable` service protocol and `ServiceKey[T]` (Rule 49).
   - Re-export keys and models in `src/harness/services/__init__.py`.
3. **Forge Sandboxed Plugin (`plugins/<category>/<name>/`)**:
   - `plugin.json`: Subprocess isolation (`IsolationMode.SUBPROCESS`, Rule 5) with declared entrypoints.
   - `service.py`: Service implementation with explicit pipe draining in `finally` blocks (Rule 14).
   - `main.py`: `HarnessPlugin` subclass exporting module singleton `plugin = ...` (Rule 45) and top-level entrypoint functions.
   - `test_<name>.py`: Contract test validating lifecycle, IoC resolution, and `PluginValidator.validate_sync` compliance (Rule 34, Rule 38).

> **Completion criterion**: Skill and plugin packages scaffolded with full manifest and protocol compliance.

---

## 5. Verification Suite, Bounded Self-Repair & Ecosystem Registration

Validate correctness, repair defects automatically, and synchronize ecosystem routing:

1. **Execute Test Contracts**:
   - Run `pytest tests/test_<skill_name>.py -v`.
   - Run `pytest plugins/<category>/<name>/test_<name>.py -v`.
   - Run `pytest tests/test_skills_hygiene.py -k "TestSkillsEcosystemHygiene" -v`.
2. **Enforce Bounded In-Flight Self-Repair Loop**:
   - If tests fail, inspect exact diagnostics and apply targeted repairs to code or test contracts.
   - **Hard Circuit Breaker**: Halt after a maximum of **3 repair attempts** before escalating.
3. **Synchronize Ecosystem Governance**:
   - Register member plugin and member skill in `CONTEXT-MAP.md` under the appropriate domain.
   - Reindex the Skill Knowledge Graph: `$env:PYTHONPATH="src"; python -m harness.cli skills graph`.
   - Verify context linter: `$env:PYTHONPATH="src"; python -m harness.commands.context lint --root .`.
   - Compile comprehensive walkthrough artifact in `<artifact_dir>/walkthrough.md`.

> **Completion criterion**: 100% tests pass, CONTEXT-MAP updated, skill graph indexed, and walkthrough compiled.

---

## The Three Foundational Pillars

### 1. The Triad Convergence Pillar
Never run isolated, disconnected audits. Always synthesize repo analysis directly into tangible, production-grade assets: verified Knowledge Items, slotted agent skills, and sandboxed micro-kernel plugins.

### 2. Mandatory Human Checkpoint Pillar
Never commit knowledge items or persist unverified skills without presenting interactive checkpoints (`ask_question`) and visual briefs in `%TEMP%` for human validation.

### 3. Subprocess Isolation & Defensive Hygiene
All external repository code must execute behind subprocess sandboxes with explicit pipe disposal (`finally` blocks) and slotted/frozen dataclass immutability.

---

## Anti-Patterns

- **Disconnected Audit Reports** — Emitting passive markdown analysis reports without scaffolding executable skills or sandboxed plugins.
- **Bypassing Interactive Checkpoint** — Committing speculative Knowledge Items to `.harness/knowledge/` without interactive user approval.
- **Monolithic Plugin Sprawl** — Bundling disparate tools into a single monolithic plugin instead of single-responsibility domain partitioning (Rule 18).
- **Infinite Self-Repair Thrashing** — Continuing failing test execution beyond the strict 3-attempt circuit-breaker limit.
- **Unvalidated Subprocess Transports** — Omitting `finally` block pipe draining (`stdout.close()`, `stderr.close()`) on subprocess runners (Rule 14).
- **Single-File Vault Pollution** — Dumping flat JSON files into `.harness/knowledge/` instead of the canonical dual-file directory format (Rule 40).
