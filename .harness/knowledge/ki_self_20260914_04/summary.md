# Slotted Triad Pipeline & Dual-Mode Visual Brief Synthesis Invariant

## Executive Summary
This Knowledge Item captures the foundational patterns governing repository inspection, slotted domain models, and visual brief generation across the triad forge and deep repository auditor pipelines, grounded in **Rule 12** (*Slotted & Frozen Dataclass Architecture*) and **Rule 51** (*F-String Dynamic Template Escaping & Multi-Brace Invariant*).

## Architectural Mechanics
1. **Slotted Immutable Value Objects**:
   - High-volume data contracts (`RepoInspectionResult`, `KiCandidate`, `TriadExecutionResult`) enforce `slots=True` and `frozen=True`.
   - `__post_init__` validation guards against empty repository identifiers, unanchored candidates, or invalid score ranges.
2. **Noise-Excluding AST & Manifest Scanner**:
   - Directory scanners proactively prune noisy directories (`.git`, `node_modules`, `.venv`, `dist`, `.harness`, `.system_generated`, `3rdparty`) during directory walks (`os.walk`), preventing performance cliffs on large monorepos.
   - Calculates 5-dimensional complexity (Span, Depth, Concurrency, Rigor, Heterogeneity) directly from AST and manifest analysis.
3. **Dual-Mode Visual Brief Generation**:
   - Generates interactive, self-contained HTML visual briefs (`compute-assessor`, `data-topology-review`, `repo-reader`) with Tailwind CSS and Mermaid diagrams in `%TEMP%`.
   - Strictly isolates CSS rules and Javascript payloads from Python f-strings or enforces double braces (`{{`, `}}`) to prevent template interpolation crashes.

## Verifiable Isnad Lineage
- **Source Seams**: `.agents/skills/repo-triad-forge/scripts/triad_pipeline.py:19-156`, `plugins/software_engineering/repo_triad_forge/service.py:32-82`.
- **Governing Invariants**: `AGENTS.md` Rule 12, Rule 50, Rule 51.
