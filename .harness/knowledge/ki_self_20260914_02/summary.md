# Diátaxis 4-Quadrant Docs-as-Code Synchronization Pipeline

## Executive Summary
This Knowledge Item codifies the Docs-as-Code documentation synchronization pipeline that bridges Daniele Procida's 4-quadrant Diátaxis framework (Tutorials, How-To Guides, Reference, Explanation) with automated AST documentation linting and C4 system topologies.

## Architectural Mechanics
1. **Master Catalog & Hub Architecture**:
   - Maintain master Diátaxis documentation hubs: `.agents/skills/README.md` for all 50 agent skills, and `plugins/README.md` plus 11 category READMEs for all 95 plugins.
   - Every catalog embeds Mermaid C4 Level 1 (System Context) and Level 2 (Container Runtime Architecture) diagrams.
2. **Business Outcome Translation**:
   - Technical documentation must explicitly link architectural invariants to business velocity: reduced model hallucination rates, lower token expenditure, and guaranteed audit compliance.
3. **Grandparent & Parent Scope Resolution in AST Audits**:
   - Subroutines and modules encapsulated in `scripts/`, `examples/`, `commands/`, and `bin/` directories must look up grandparent `SKILL.md` (`f.parent.parent / "SKILL.md"`) or parent package `README.md` before flagging an unlinked module deficit.
4. **Markdown AST Linter Isolation (Rule 47)**:
   - Linting engines must strip fenced code blocks (```` ```...``` ````) and inline backticks using negative lookaround assertions before verifying link integrity, preventing false-positive flags on typed annotations like `ServiceKey[T]`.

## Verifiable Isnad Lineage
- **Grounding Trajectories**: `b1c6bfd4` (50 skills synchronized), `b3e348b3` (95 plugins across 11 categories synchronized), `e8a84c34` (repo-doc-synchronizer inception).
- **Governing Invariants**: `AGENTS.md` Rule 11, Rule 44, Rule 47.
