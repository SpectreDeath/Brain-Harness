---
name: context-anti-rot-sync
description: Audit, prune, synchronize, and lint multi-layer codebase context files across agent configurations. Enforces Rule 11 line limits, eliminates lint leakage, and synchronizes single-source instructions. Do not use for generic prose editing or creative writing.
---

# Context Anti-Rot Sync: Automated Hygiene & Synchronization

`context-anti-rot-sync` packages the end-to-end operational workflow for maintaining codebase context health, eliminating instruction rot, pruning lint leakage, and synchronizing single-source rules across coding agent tools.

## Dependencies

This workflow coordinates and reuses the following core skills:
- [`codebase-context-governor`](../codebase-context-governor/SKILL.md): Orchestrates 5-stage context governance and compute tier assessment.
- [`codebase-context-architect`](../codebase-context-architect/SKILL.md): Provides context synchronization engines and multi-agent projection rules.
- [`agent-instruction-architect`](../agent-instruction-architect/SKILL.md): Enforces instruction file boundaries, seam definitions, and negative constraints.
- [`compute-model-assessor`](../compute-model-assessor/SKILL.md): Assesses 5D complexity to calibrate reasoning budgets.

## Quick Start

```bash
# Option A: One-Shot Composite Context Hygiene Execution (Recommended)
python .agents/skills/context-anti-rot-sync/scripts/context_sync_cli.py run --target AGENTS.md --output %TEMP%/context_sync_report.json

# Option B: Granular Multi-Step Execution
# 1. Audit AGENTS.md for line-count overflow (>150 lines) and lint leakage
python .agents/skills/context-anti-rot-sync/scripts/context_sync_cli.py audit --target AGENTS.md --output %TEMP%/audit_report.json

# 2. Prune redundant whitespace and enforce negative boundaries
python .agents/skills/context-anti-rot-sync/scripts/context_sync_cli.py clean --target AGENTS.md --output %TEMP%/cleaned_agents.md

# 3. Synchronize canonical instructions to secondary agents (CLAUDE.md, .cursorrules)
python .agents/skills/context-anti-rot-sync/scripts/context_sync_cli.py sync --source AGENTS.md --output %TEMP%/sync_manifest.json

# 4. Run automated anti-rot linter suite across all context files
python .agents/skills/context-anti-rot-sync/scripts/context_sync_cli.py lint --output %TEMP%/lint_results.json
```

## Utility Scripts

The companion CLI script `scripts/context_sync_cli.py` delegates to `context_sync_engine.py` and implements both composite and modular subcommands:

- `run`: Executes the complete context hygiene pipeline (audit, clean, sync, and workspace lint) in a single atomic pass.
- `audit`: Scans instruction files for bloat, line-count overflow (>150 lines), token budget violations, and lint leakage. Writes full diagnostic findings to `--output <file.json>`.
- `clean`: Applies deterministic rule trimming, eliminates tutorial prose, deduplicates whitespace, and formats command palettes. Writes cleaned file to `--output <file.md>`.
- `sync`: Evaluates primary manifest against derived target configs (`CLAUDE.md`, `.cursorrules`), projecting shared rules without manual copy-paste.
- `lint`: Verifies all context files against line limits, frontmatter character budgets (100–350 chars), link formats, and delimiter syntax.

## Workflow Stages

### Stage 1: Context Rot & Line Audit
Scan all instruction files in the workspace for Rule 11 violations (lines > 150), transient lint dumps, and conflicting command palettes.
> **Completion criterion**: Concrete list of target line-count and smell violations cataloged in JSON audit report.

### Stage 2: Deterministic Cleanse
Prune conversational narrative and redundant examples while strictly preserving execution seams (build/test/lint) and negative boundaries ("what NOT to touch").
> **Completion criterion**: Sanitized instruction file bounded strictly within $\le 150$ lines.

### Stage 3: Single-Source Synchronization
Propagate updated invariants from the canonical manifest (`AGENTS.md`) to secondary tool instructions without divergence or semantic drift.
> **Completion criterion**: All derived client instruction files synchronized with zero manual editing errors.

### Stage 4: Mandatory Checkpoint
Generate an interactive audit brief and review report. Author an `implementation_plan.md` artifact if structural edits exceed threshold, and await explicit user confirmation before applying file changes.
> **Completion criterion**: Explicit user confirmation received before in-place modification of repository context files.

### Stage 5: Automated Anti-Rot Linting
Execute continuous verification through `context_sync_cli.py lint` to assert that all files pass line count, frontmatter budget, and link checks.
> **Completion criterion**: 100% linter rules pass with zero critical warnings across all repository context files.

## Visual Brief

When audit findings indicate structural drift or line-count bloat $\ge 150$ lines, generate an interactive HTML status report saved to `%TEMP%/context-anti-rot-review-<timestamp>.html` rendering a before/after line-count comparison table and Mermaid synchronization DAG.

## Anti-Patterns

- **Instruction Bloat** — Expanding instruction files beyond 150 lines with tutorials, generic API documentation, or prose explanations.
- **Transient Lint Leakage** — Pasting transient compiler errors, tracebacks, or linter reports directly into persistent instruction files.
- **Manual Divergent Sync** — Manually editing secondary agent files (`CLAUDE.md`, `.cursorrules`) instead of projecting from the canonical SSOT manifest.
- **Bypassing Negative Boundaries** — Removing explicit "what NOT to touch" sections, allowing agent edits to bleed into forbidden directories.
