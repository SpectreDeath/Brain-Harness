---
name: codebase-context-governor
description: Audit, partition, budget, and enforce multi-layer codebase context files across coding agents. Eliminates context rot through Three-Layer boundaries, automated CI linters, and dynamic compute tier calibration. Do not use for generic prompt writing.
---

# Codebase Context Governor: Multi-Agent Context Lifecycle & Budgeting

`codebase-context-governor` is an authoritative composite meta-skill that orchestrates the governance, partitioning, linting, and synchronization of codebase context files (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules/`) across heterogeneous AI coding agents.

It coordinates four specialized capabilities:
1. **Multi-Layer Context Architecture & Synchronization** ([`codebase-context-architect`](../codebase-context-architect/SKILL.md))
2. **Repository Instruction Hygiene & Boundary Enforcement** ([`agent-instruction-architect`](../agent-instruction-architect/SKILL.md))
3. **Enterprise Skill Specification & Progressive Governance** ([`agent-skills-architect`](../agent-skills-architect/SKILL.md))
4. **5D Dynamic Compute & Reasoning Tier Assessment** ([`compute-model-assessor`](../compute-model-assessor/SKILL.md))

See [CARD.md](CARD.md) for the companion summary card, 5-stage progression matrix, and invariants checklist.
Consult `/codebase-context-architect` for synchronization engines, `/agent-instruction-architect` for negative boundary guidelines, and [governance-playbook.md](references/governance-playbook.md) for governance playbooks.

---

## The 5-Stage Context Governance Progression

```
[1. Smell & Budget Audit] ──► [2. Three-Layer Partitioning] ──► [3. SSOT Synchronization]
                                                                        │
                                                                        ▼
[5. Dynamic Compute Calibration] ◄── [4. Automated CI Linter Enforcement] ◄─────┘
```

---

## 1. Context Rot & Smell Auditing

Conduct a comprehensive scan across all agent context and instruction files in the workspace:

1. **Smell Diagnostics (Rule 11)**:
   - Identify **Lint Leakage**: Repetitive compiler/linter error lists that pollute context windows.
   - Identify **Context Bloat**: Instruction files exceeding 150 lines or 4,000 tokens.
   - Identify **Instruction Contradiction**: Divergent commands or architectural patterns across competing tool files.
2. **Verify Execution Seams**:
   - Confirm explicit build, test, and lint commands are defined with zero ambiguity.
3. **Inspect Negative Boundaries**:
   - Confirm explicit "what NOT to touch" boundaries are present in instruction files.

> **Completion criterion**: Context smell diagnostic scorecard generated with token budget violations and line count hotspots isolated.

---

## 2. Three-Layer Context Partitioning

Partition unstructured context into three strictly bounded architectural layers:

1. **Layer 1: Constitution & Kernel Invariants**:
   - System identity, core security boundaries, immutable architectural invariants (Rule 1 to Rule 44).
2. **Layer 2: Project Execution Seams (SSOT)**:
   - Command palettes, test contracts, domain taxonomies, and modular plugin directories.
   - Preserved under canonical instruction files (`AGENTS.md`).
3. **Layer 3: Ephemeral Task Context**:
   - Session trajectories, sub-agent task allocations, and in-flight transaction states.

> **Completion criterion**: Codebase context partitioned across all 3 layers with zero cross-layer bleeding.

---

## 3. Single Source of Truth (SSOT) Synchronization

Synchronize derived context files from primary repository manifests:

1. **Single Source Generation**:
   - Derive agent tool lists, plugin registries, and CLI schemas from active workspace code rather than manual copy-paste.
2. **Cross-Agent Export**:
   - Project shared architectural rules into client-specific locations (`CLAUDE.md`, `.cursorrules`) using deterministic generators.
3. **Preserve Custom Overrides**:
   - Support zero-fork configuration layers (`config.default.yaml` vs `.agents/skills.config.yaml`).

> **Completion criterion**: All agent context files synchronized against SSOT with zero drift detected.

---

## 4. Automated CI Linter Enforcement

Embed context validation into continuous integration and pre-commit pipelines:

1. **Context Linter Execution (Rule 10)**:
   - Execute `harness context lint` to assert line counts ($\le 150$ lines for instructions), token limits, and link integrity.
2. **Format & Delimiter Verification**:
   - Verify frontmatter budgets ($100 \le \text{chars} \le 350$) and ASCII delimiter syntax (Rule 37).
3. **Git Pre-Commit Seams**:
   - Block commits that introduce unbudgeted instruction files or malformed YAML configs.

> **Completion criterion**: CI linter passes 100% with zero critical warnings across all repository context files.

---

## 5. Dynamic Compute Model Assessment

Evaluate the governed repository state and calibrate optimal reasoning compute budgets:

1. **5D Complexity Evaluation (Rule 25)**:
   - Score repository Span, Depth, Concurrency, Rigor, and Domain Heterogeneity.
2. **Thinking Budget Calibration**:
   - Route agent sessions to optimal reasoning tiers (High, Medium, Low, Off) calibrated for target foundation models.
3. **Subprocess Timeout Scaling**:
   - Dynamically adjust async subprocess runner timeouts to prevent false-positive watchdog terminations during deep refactors.

> **Completion criterion**: Compute tier recommendation and reasoning budget calibrated for current codebase complexity.

---

## The Three Foundational Pillars

### 1. The Visual Brief Pillar
Every context governance cycle renders an interactive HTML visual brief in `%TEMP%` displaying layer allocation pie charts, line count distributions, and token budget gauges.

### 2. The Mandatory Checkpoint Pillar
The agent must never prune, truncate, or rewrite repository instruction files without first presenting `implementation_plan.md` with `RequestFeedback: true` and awaiting explicit user confirmation.

### 3. Explicit Anti-Patterns
Rigid architectural boundaries prevent context bloating, instruction drift, and silent linter bypasses.

---

## Anti-Patterns

- **Unbounded Instruction Bloat** — Allowing `AGENTS.md` or `CLAUDE.md` to exceed 150 lines or contain verbose tutorials.
- **Lint Leakage Infiltration** — Pasting transient linter warnings or error logs directly into persistent agent instruction files.
- **Multi-Source Instruction Drift** — Maintaining duplicate manual rule sets across different agent files instead of generating from SSOT.
- **Static Reasoning Misallocation** — Running heavy reasoning models on trivial tasks or starving complex multi-agent audits of compute budget.
- **Unchecked Link Rot** — Maintaining dead markdown links or invalid symbol anchors in context files.
- **Missing Negative Boundaries** — Specifying agent permissions without explicit negative constraints ("Do not edit...").
