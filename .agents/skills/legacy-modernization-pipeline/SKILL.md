---
name: legacy-modernization-pipeline
description: Execute safe legacy codebase modernization through multi-axis repository audits, causal DAG topology mapping, characterization test safety nets, and adversarial refactoring loops. Do not use for greenfield project scaffolding or trivial single-file edits.
---

# Legacy Modernization Pipeline: Safe Architectural Transformation

`legacy-modernization-pipeline` is an authoritative composite meta-skill that orchestrates the end-to-end modernization of complex, unfamiliar, or high-risk legacy codebases without breaking production invariants or altering observable behavior.

It coordinates five specialized engineering disciplines:
1. **Multi-Axis Codebase Auditing** ([`deep-repo-auditor`](../deep-repo-auditor/SKILL.md))
2. **Causal DAG & Data Topology Mapping** ([`data-topology-mapper`](../data-topology-mapper/SKILL.md))
3. **Characterization Testing & Safety Nets** ([`legacy-refactoring-guardian`](../legacy-refactoring-guardian/SKILL.md))
4. **Inspect-Before-Edit Adversarial Verification** ([`adversarial-agent-verifier`](../adversarial-agent-verifier/SKILL.md))
5. **Architectural Deepening & Seam Elevation** ([`deepen-architecture`](../deepen-architecture/SKILL.md))

See [CARD.md](CARD.md) for the companion summary card, 5-stage progression matrix, and invariants checklist.
Consult `/legacy-refactoring-guardian` for characterization patterns, `/adversarial-agent-verifier` for seam verification, and [characterization-patterns.md](references/characterization-patterns.md) for characterization test patterns.

---

## The 5-Stage Modernization Pipeline Progression

```
[1. Multi-Axis Audit] ──► [2. DAG Topology Mapping] ──► [3. Characterization Safety Net]
                                                                  │
                                                                  ▼
[5. Architectural Deepening] ◄── [4. Adversarial Refactor & Verify] ◄─────┘
```

---

## 1. Multi-Axis Repository Audit

Survey the legacy target codebase across 4 fundamental axes before authoring any test contracts or modifying code:

1. **Static Complexity & Volume Profiling**:
   - Inspect cyclomatic complexity, directory depth, dependency graphs, and code-to-comment ratios.
   - Profile hotspot files exhibiting high churn and low test density.
2. **5D Compute & Complexity Scoring**:
   - Evaluate Span, Depth, Concurrency, Rigor, and Heterogeneity.
   - When score $\ge 0.75$, lock reasoning model tier to High and extend subprocess timeouts (Rule 25).
3. **Seam Identification**:
   - Map entrypoints, I/O boundaries, database bindings, and global singletons.

> **Completion criterion**: Multi-axis audit report formulated with blast radius boundaries and target seam candidates isolated.

---

## 2. Causal DAG Topology Mapping

Construct a rigorous directional acyclic graph of data flow, state mutation, and dependency lifecycles:

1. **Map State Flow & Side Effects**:
   - Trace all mutable global state, implicit environment variables, and hidden filesystem side effects.
   - Chart caller-callee hierarchies around candidate refactoring zones.
2. **Isolate Coupling Bottlenecks**:
   - Identify circular dependencies, God classes, and tangled cross-module imports.
3. **Derive Invariant Seams**:
   - Pin down immutable domain rules that must remain constant throughout transformation.

> **Completion criterion**: Causal DAG diagram and seam boundaries documented in `%TEMP%` visual brief.

---

## 3. Characterization Safety Nets

Wrap legacy components in airtight characterization tests ("golden master tests") before changing a single line of production code:

1. **Black-Box Input/Output Capture**:
   - Author characterization suites that record outputs for known input matrices, boundary inputs, and edge cases.
   - Capture side effects (log emissions, filesystem modifications, event dispatches).
2. **Direct Mutation & Failure Verification**:
   - Temporarily inject synthetic mutations into the legacy module to guarantee the test suite fails loudly.
3. **Lock Down Behavior**:
   - Baseline characterization coverage $\ge 90\%$ over the target refactoring zone.

> **Completion criterion**: Characterization test suite passes 100% on unmodified legacy code and fails on injected behavioral mutations.

---

## 4. Adversarial Refactor & Seam Isolation

Execute surgical refactoring inside strict transactional boundaries:

1. **Inspect-Before-Edit Protocol (Rule 13)**:
   - Perform read-only AST inspection of target functions and assert failing contracts prior to modification.
2. **Introduce Clean Seams**:
   - Extract interfaces, replace singleton couplings with typed service keys (`ServiceKey[T]`, Rule 2), and introduce slotted value objects (`slots=True, frozen=True`, Rule 12).
3. **In-Flight Self-Repair & Linter Gates (Rule 16)**:
   - Run diagnostics immediately upon file modification; repair bracket, syntax, or typing errors in-flight.
4. **Adversarial Diff Verification**:
   - Demand minimal git diffs with zero unrelated file mutations or whitespace noise.

> **Completion criterion**: Characterization tests pass green against modernized implementation with verified git diff.

---

## 5. Architectural Deepening & Verification

Deepen module interfaces and formalize architectural invariants:

1. **Elevate Module Depth**:
   - Collapse shallow pass-through shims; provide high-leverage abstractions with simple public APIs hiding internal complexity.
2. **End-to-End Contract Verification**:
   - Run complete unit, integration, and regression suites.
3. **Commit Architectural Learnings**:
   - Scaffolding canonical Knowledge Vault dual-file items (`metadata.json` + `summary.md`) capturing modernized patterns and decision heuristics.

> **Completion criterion**: Full test suite passes green, architectural depth validated, and Knowledge Vault item committed.

---

## The Three Foundational Pillars

### 1. The Visual Brief Pillar
Every modernization run must render an interactive HTML visual brief in `%TEMP%` displaying the legacy dependency DAG, characterization coverage heatmaps, and side-by-side refactoring diffs.

### 2. The Mandatory Checkpoint Pillar
The agent must never author refactored code or delete legacy implementations without first presenting `implementation_plan.md` with `RequestFeedback: true` detailing the characterization test evidence.

### 3. Explicit Anti-Patterns
Rigid boundaries prevent speculative rewriting, unpinned behavioral changes, and big-bang refactoring disasters.

---

## Anti-Patterns

- **Speculative Greenfield Rewriting** — Throwing away legacy implementations without characterization safety nets or understanding tacit domain edge cases.
- **Unpinned Behavior Mutation** — Modifying legacy code before characterization tests are written and verified with synthetic mutations.
- **Big-Bang Scope Explosion** — Refactoring entire directory trees simultaneously rather than isolating atomic, test-bounded seams.
- **Shallow Shim Proliferation** — Wrapping messy legacy methods in thin pass-through adapters without elevating interface depth or eliminating root coupling.
- **Single-File Vault Pollution** — Dumping single flat JSON files into `.harness/knowledge/` instead of the canonical dual-file directory (`metadata.json` + `summary.md`).
- **Unchecked Blast Radius** — Modifying public interfaces or database schemas without verifying all downstream consumers in the causal DAG.
