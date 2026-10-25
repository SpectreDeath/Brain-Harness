# Interpretable Context Methodology (ICM): Folder Structure as Agent Architecture

**ID:** `ki_20261024_icm_architect`  
**Literature:** Van Clief & McDermott, *Interpretable Context Methodology: Folder Structure as Agent Architecture*, arXiv:2603.16021 (2026)  
**Source Repository:** `https://github.com/RinDig/Interpretable-Context-Methodology.git` (Commit: `02ba5d8`, with upstream `RinDig/icm-architect.git` `8bc2f56`)  
**Status:** `VERIFIED`

---

## 1. Epistemic Foundation & Core Thesis

Traditional AI agent systems rely heavily on complex multi-agent orchestration frameworks (such as LangGraph, CrewAI, AutoGen) or monolithic prompts spanning 30,000–50,000 tokens. These approaches suffer from severe context bloat, non-deterministic branching, silent failure cascades, and opaque runtime state.

**Interpretable Context Methodology (ICM)** proves that **folder structure can serve directly as agent architecture**:
1. **Numbered folders carry sequencing**: Workflows flow sequentially through numbered directories (`01_research`, `02_script`), where stage $N$ outputs become stage $N+1$ inputs.
2. **Folder hierarchy carries context scoping**: A 5-layer hierarchy isolates routing from working contracts, guaranteeing per-step contexts remain strictly under 8,000 tokens.
3. **Plain markdown files carry state**: World state lives on disk as inspectable markdown files; any human or agent can audit system status without executing code.
4. **Every step terminates at an auditable check**: Outputs are evaluated by human review, deterministic scripts, or small models emitting `check.md` (`pass` or `fail: <reason>`), stopping errors before downstream contamination.

---

## 2. The Five-Layer Context Hierarchy (L0–L4)

| Layer | File / Location | Question Answered | Operational Role | Target Size |
|---|---|---|---|---|
| **L0** | `AGENTS.md` | Where am I? | Identity & Routing Catalog | < 60 lines (~500 tokens) |
| **L1** | root `CONTEXT.md` | Where do I go? | Pipeline & Schema Map | 200–500 tokens |
| **L2** | stage `CONTEXT.md` | What do I do? | **The Control Point** (Inputs, Process, Outputs, Check) | 200–500 tokens |
| **L3** | `_shared/`, `references/` | What rules apply? | Factory (Stable across runs) | 500–2,000 tokens |
| **L4** | `stages/*/output/` | What am I making? | Product (Per-run working artifacts) | Task-bounded |

---

## 3. The Three Primitives & Five Canonical Forms

All ICM workspaces are composed from three fundamental structural primitives:
- **Sequence**: Numbered steps (`01_`, `02_`) where each stage handoff is an editable file.
- **Shelf**: A folder of same-shaped records or nodes (`records/`, `teams/`, `concepts/`).
- **Catalog**: A small, stable routing file (`AGENTS.md`, `_index.md`) that points down and holds no content.

These compose into five canonical forms:
1. **Pipeline**: Production line for repeatable deliverables (e.g. video creation, document generation).
2. **Record Library**: Uniform entity records accumulating lifecycle status (e.g. clients, sessions, patients).
3. **Knowledge Bundle**: Linked concepts, claims, plans, and raw sources with verbatim quote provenance.
4. **Context Map**: Organizational graph of teams, processes, and systems linked by `consumes:` / `produces:`.
5. **System Map**: Codebase audit hierarchy with nouns, verbs, and impact indexes.

---

## 4. The 10 Mandatory Invariants

1. **One folder, one job**: Each folder performs a single step or holds one kind of entity.
2. **Small, stable entry file**: `AGENTS.md` is strictly under 60 lines, routing only with zero content payload.
3. **Numbering encodes order**: `01_`, `02_` prefixes where sequence matters.
4. **Every working folder has a contract**: `CONTEXT.md` defining Inputs, Process, Outputs, and Check.
5. **Factory vs. product split**: Stable reference materials (`_shared/`) separate from working outputs.
6. **Every step ends at a check**: Output must pass an explicit check emitting `check.md` before downstream consumption.
7. **Load only what the step needs**: Full step context remains under 8,000 tokens.
8. **Plain text, linkable, queryable**: Relative links resolve cleanly; YAML frontmatter labels enable indexing.
9. **Status lives on disk**: Status is readable from filesystem state and generated `_index.md` files.
10. **Instantiate by copying**: New units of work are copies of templates from `_templates/`, never blank pages.

---

## 5. Decision Heuristics & Anti-Pattern Defenses

- **When to use ICM**: Sequential, checked, repeatable knowledge work (data engineering, document synthesis, multi-stage pipelines, codebase audits).
- **When NOT to use ICM**: Real-time multi-agent concurrent collaboration, high-concurrency multi-user serving, or mid-pipeline automated dynamic branching (use framework code instead).
- **The U-Curve of Human Editing**: Expect heavy human checks at the first stage (direction-setting), light in the middle (constrained by anchors), and heavy at the final deliverable. Design first and last stage outputs to be especially editable.
- **The Cold Walk Test**: Always verify workspaces by walking them cold as an agent with no memory: Where am I? Exact inputs? Disk status? Zero content in catalog? One home per fact? Links resolve? Under 8k tokens? Broken invariants explained?
