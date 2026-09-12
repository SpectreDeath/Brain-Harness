---
name: repo-doc-synchronizer
description: Audit repository documentation coverage, detect doc drift against live code signatures, update stale references, and author missing Diátaxis documentation suites. Do not use for generic copyediting or non-technical prose.
---

# Repository Documentation Synchronizer

`repo-doc-synchronizer` audits codebase documentation coverage, identifies stale or missing documentation across packages and plugins, and authors standardized technical documentation suites conforming to the Diátaxis taxonomy.

See [CARD.md](CARD.md) for companion cheat sheets, CLI triggers, and invariant checklists.

---

## Overview

The skill operationalizes documentation as an active engineering contract ("Docs-as-Code"):
- **AST Symbol Inspection**: Extracts classes, callables, type annotations, and docstrings via static analysis.
- **Coverage Auditing**: Quantifies module documentation health (docstrings, public symbol coverage, dedicated Markdown guides).
- **Drift Detection**: Flags broken local file links and stale symbol signatures in existing documentation.
- **Diátaxis Scaffolding**: Synthesizes structured API references, how-to recipes, and package READMEs populated with live AST data.
- **Visual Briefs**: Emits interactive Mermaid.js diagrams illustrating coverage topology before making modifications.

---

## Dependencies

- **[developer-docs-architect](../developer-docs-architect/SKILL.md)**: Dispatched for deep Diátaxis quadrant authoring (API specs, C4 Mermaid architecture models, and developer guides).
- **[codebase-context-architect](../codebase-context-architect/SKILL.md)**: Dispatched when synchronizing multi-layer agent context files (`AGENTS.md`, `CLAUDE.md`).
- **[crafting-skills](../crafting-skills/SKILL.md)**: Followed for skill formatting, visual briefs, and summary cards.

---

## Quick Start

### 1. Audit Repository Documentation Coverage
```bash
python .agents/skills/repo-doc-synchronizer/scripts/doc_synchronizer.py audit --root . --output coverage_scorecard.json
```

### 2. Detect Documentation Drift and Broken Links
```bash
python .agents/skills/repo-doc-synchronizer/scripts/doc_synchronizer.py drift-check --root . --output drift_report.json
```

### 3. Generate Interactive Visual Coverage Brief
```bash
python .agents/skills/repo-doc-synchronizer/scripts/doc_synchronizer.py visual-brief --root . --output %TEMP%/doc_brief.html
```

### 4. Scaffold Missing Diátaxis Documentation
```bash
python .agents/skills/repo-doc-synchronizer/scripts/doc_synchronizer.py scaffold --module src/harness/services/agentwikis.py --type api --output docs/api/agentwikis.md
```

---

## Utility Scripts

The skill provides `scripts/doc_synchronizer.py` with four deterministic subcommands:

1. **`audit`**:
   - Analyzes Python modules against Markdown docs.
   - Flags files with missing docstrings or missing dedicated documentation.
   - Calculates overall coverage percentage against `--min-coverage` threshold.
2. **`drift-check`**:
   - Strips code blocks to eliminate false positives per Rule 47.
   - Verifies relative markdown links against active filesystem files.
3. **`scaffold`**:
   - Ingests a module via AST.
   - Pre-populates clean Diátaxis documentation templates (`api`, `readme`, `howto`).
4. **`visual-brief`**:
   - Generates a self-contained HTML file rendering a dark-mode Mermaid diagram showing documented vs. deficit modules.

---

## Workflow: 4-Stage Execution Loop

### Stage 1: Documentation Coverage Audit
1. Execute the `audit` subcommand across target modules or plugins.
2. Inspect the generated JSON coverage scorecard to identify undocumented public classes, methods, and modules.

### Stage 2: Drift & Integrity Inspection
1. Execute `drift-check` across documentation directories (`docs/`, `plugins/`).
2. Identify broken relative links or stale symbol names resulting from code refactoring.

### Stage 3: Visual Brief & Human-in-the-Loop Review
1. Render an interactive HTML visual brief using `visual-brief`.
2. Present findings and planned additions to the user via `implementation_plan.md`.
3. Halt and await explicit user approval before writing or updating documentation files.

### Stage 4: Synthesis, Scaffolding & Verification
1. **Package-Level Diátaxis Scaffolding**: Prioritize authoring package-level `README.md` guides for core packages (`src/harness/commands/`, `src/harness/bridges/`) and plugins (`plugins/<category>/<plugin>/`). A package `README.md` elevates all sibling modules by providing live AST symbol tables and manifest metadata without generating file sprawl.
2. Scaffold missing documentation using `scaffold` with appropriate Diátaxis quadrant templates.
3. Update existing documentation files to repair broken links and update function signatures.
4. Re-run `drift-check` and `audit` to verify 100% resolution of coverage deficits.

---

## Anti-Patterns

- **Premature File Mutation** — Modifying existing documentation or creating new files without first auditing AST symbols and presenting an implementation plan.
- **Ungrounded Prose** — Writing speculative narrative text instead of deriving class and function documentation directly from active AST syntax trees.
- **Broken Relative Links** — Writing workspace-absolute `file:///` URIs or unverified links that break in sandboxes or CI environments.
- **Monolithic Conflation** — Combining tutorials, architecture rationale, and reference tables on a single page instead of adhering to Diátaxis quadrants.
