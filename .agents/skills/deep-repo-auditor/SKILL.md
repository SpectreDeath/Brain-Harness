---
name: deep-repo-auditor
description: Execute multi-axis repository audits combining compute model assessment, structural data topology mapping, 4-axis codebase introspection, and knowledge/skill distillation. Trigger when auditing large foreign codebases, evaluating agent harnesses, mapping architecture blast radius, or running multi-agent repository distillation pipelines.
---

# Deep Repo Auditor: Multi-Axis Codebase & Harness Auditing Engine

`deep-repo-auditor` is the unified cognitive audit engine for Brain Harness. It synthesizes task compute budgeting, structural data topology mapping, 4-axis codebase introspection, and structured artifact scouting into a deterministic five-stage auditing pipeline that distills foreign repositories into actionable Knowledge Items (KIs) and production-grade agent skills.

Every audit session follows a strict five-stage progression:

```
[1. Compute & Surface Assessment] → [2. Structural & Data Topology Mapping] → [3. 4-Axis Codebase Matrix] → [4. Visual Briefs & Synthesis Checkpoint] → [5. Knowledge & Skill Extraction]
```

See [CARD.md](CARD.md) for the companion summary card, dimensional scoring matrix, and invariants checklist.
Consult `/repo-reader` for detailed Git trajectory queries, `/data-topology-mapper` for graph blast radius analysis, and `/crafting-skills` for skill authoring standards.

---

## 1. Compute & Surface Assessment

Assess the complexity and operational boundary of the target codebase before deep scanning:

1. **Dimensional Complexity Scoring**:
   - Evaluate across 5 dimensions: **Ambiguity**, **Span** (multi-package/monorepo layers), **Depth** (AST/logic complexity), **Rigor**, and **Concurrency** (async event loops, lifecycle hooks).
   - Produce a `ComplexityVector` and project compute requirements.
2. **Model Tier & Thinking Allocation**:
   - *High Complexity*: Gemini 3.7 Flash (`HIGH` thinking, 16k tokens) or Claude 3.7 Sonnet (16k thinking).
   - *Medium Complexity*: Gemini 3.7 Flash (`MEDIUM` thinking, 4k tokens).
3. **Boundary & Snapshot Detection**:
   - Inspect whether the target path is outside the IDE workspace sandbox (use shell execution fallbacks with host `Cwd` when direct file access is restricted).
   - Detect nested root directories (e.g. `repo-master/repo-master`) and identify if the directory is a non-Git snapshot without `.git`.
   - **Nested Root Resolution Algorithm**: Walk from the provided path inward, probing each level for canonical manifest files (`pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, `pom.xml`). The deepest directory containing a manifest is the true project root. Log the nesting depth to avoid re-discovering on subsequent stages.

> **Completion criterion**: Task scored across 5 complexity dimensions, model tier declared, and workspace access path verified.

---

## 2. Structural & Data Topology Mapping

Classify the target codebase's architectural and execution data structures:

1. **Topological Classification**:
   - **Graph of Trees**: Polyglot service networks or monorepo package ecosystems managing hierarchical module trees.
   - **Hash-Indexed Dispatcher**: Event buses and lifecycle hook registries matching events to command arrays in $O(1)$.
   - **Fan-Out / Fan-In Agent Swarm**: Multi-agent task execution topologies (e.g., parallel PR review agents aggregating to a simplifier).
   - **Priority Queue / Rewake Loop**: Asynchronous out-of-band feedback channels preempting main execution streams.
2. **Blast Radius Computation**:
   - Trace vertex-edge connections between modules, hook interceptors, and external runtime dependencies to compute the structural blast radius.

> **Completion criterion**: Core data topology identified, vertex/edge contracts mapped, and blast radius table formulated.

---

## 3. 4-Axis Codebase Introspection Matrix

Execute 4 structured introspection vectors across the mounted repository:

```
┌─────────────────────────────────────────────────────────────┐
│               4-AXIS CODEBASE INTROSPECTION                 │
├──────────────────────────────┬──────────────────────────────┤
│ Axis 1: Architecture & Seams │ Axis 2: Trajectories/Release │
│ - Plugin registries & IoC    │ - Git commits or changelogs  │
│ - Boundary isolation         │ - Evolution & breaking diffs │
├──────────────────────────────┼──────────────────────────────┤
│ Axis 3: Verification Gates   │ Axis 4: Delta Innovations    │
│ - Testing & linting regimes  │ - Async rewake lifecycles    │
│ - Structural invariant checks│ - Specialized agent swarms   │
└──────────────────────────────┴──────────────────────────────┘
```

1. **Axis 1 (Architecture & Seams)**: Map plugin architectures, lifecycle hook entrypoints, and container boundaries.
2. **Axis 2 (Trajectories & Evolution)**: Review commit histories (or `CHANGELOG.md` / release notes if `.git` is absent).
3. **Axis 3 (Verification & Standards)**: Audit testing frameworks (`vitest`, `pytest`), type systems, and invariant validation scripts.
4. **Axis 4 (Delta Innovations)**: Extract novel patterns (e.g. pattern-matched stop hooks, background LLM reviewers, specialized sub-agent prompts).

> **Completion criterion**: 4 query result batches harvested with exact source file citations.

---

## 4. Visual Briefs & Synthesis Checkpoint

Synthesize all findings into interactive HTML reports and halt for user confirmation:

1. **Generate Interactive Visual Briefs**:
   - `%TEMP%\compute-assessor-<timestamp>.html`: Dimensional complexity, cost economics, and model routing DAG.
   - `%TEMP%\data-topology-review-<timestamp>.html`: Mermaid diagram of module/agent topology and blast radius table.
   - `%TEMP%\repo-reader-<timestamp>.html`: 4-axis architectural matrix and plugin ecosystem graph.
2. **Deliver Clickable Links**: Output absolute `file:///` URLs directly to the user.
3. **Interactive Synthesis Checkpoint**:
   - Present candidate Knowledge Items (KIs) via `ask_question` with multi-select options.
   - Present the formal **Topology Specification Block**.
   - Await explicit user approval before writing persistent memory or new skills.

> **Completion criterion**: 3 Visual Briefs written to `%TEMP%` and candidate KIs approved at the checkpoint.

---

## 5. Knowledge & Skill Extraction

Persist approved learnings and synthesize discovered workflows into production-grade assets:

1. **Knowledge Item (KI) Lineage Commit**:
   - Write to `.harness/knowledge/<ki_id>/` with `metadata.json` (Isnad provenance, exact file/line links) and `summary.md`.
2. **Skill / Plugin Scaffolding**:
   - If novel reusable agent workflows or sub-agent patterns were identified, author them into `.agents/skills/<skill-name>/` following `/crafting-skills` standards.

> **Completion criterion**: Approved KIs and distilled skills committed with 100% verified provenance.

---

## In-File Reference & Vocabulary

- **Aspect Router**: An agent dispatcher that fans out work across specialized domain sub-agents (e.g., test analyzer, security hunter).
- **Async Rewake**: A mechanism where background processes asynchronously trigger agent re-engagement upon discovering actionable findings.
- **Blast Radius**: The transitive closure of modules, hooks, and dependencies affected by changing a given component.
- **Isnad Provenance**: Unbroken verification lineage linking every extracted cognitive claim to a primary source file and line coordinate.

---

## Anti-Patterns

- **Boundary Blindness** — Attempting direct file reads on sandboxed external paths without shell fallback execution.
- **Non-Git Crash** — Failing when inspecting unzipped codebase snapshots lacking `.git` instead of pivoting to changelog/manifest analysis.
- **Unanchored Claim Extraction** — Recording abstract heuristics without citing concrete source lines and manifests.
- **Monolithic Tool Bloat** — Coupling multi-agent review roles into a single giant prompt instead of fanning out to single-responsibility sub-agents.
- **F-String Brace Collision in HTML Generators** — Mixing regular Python dict/set literals with f-string HTML templates causes `{{`/`}}` escaping ambiguity. Separate data construction from template interpolation, or use `str.format()` / `string.Template` for HTML bodies containing JavaScript objects.
