# The 15 MWP/ICM Workspace Architecture Conventions

## Core Architectural Axiom
Interpretable Context Methodology (ICM) eliminates heavyweight multi-agent frameworks by establishing 15 structural conventions that transform a standard filesystem directory into an auditable, deterministic agent orchestration harness.

### 1. Stage Contracts & Predictable Handoffs
- **Pattern 1 (Stage Contracts)**: Every stage `CONTEXT.md` follows an immutable shape:
  - `## Inputs` table: `| Source | File/Location | Section/Scope | Why |`
  - `## Process`: Sequential enumerated steps
  - `## Outputs` table: `| Artifact | Location | Format |`
- **Pattern 2 (Stage Handoffs via `output/`)**: Stage $N$ writes its deliverable to `stages/0N-name/output/`. Stage $N+1$'s inputs table declares `../0N-name/output/artifact.md` as its source. Every output is an inspection and editing surface for the human before downstream stages execute.

### 2. Dependency Hygiene & Context Bounding
- **Pattern 3 (One-Way Cross-References)**: Circular references are prohibited. Dependency graphs are strictly acyclic ($A 	o B \implies B 
ot	o A$).
- **Pattern 4 (Selective Section Routing)**: Inputs tables specify exact markdown heading sections (`# Heading`) to load, preventing full-file prompt dilution.
- **Pattern 5 (Canonical Sources)**: Every rule, color, or schema lives in strictly one canonical home.
- **Pattern 6 (Flat File Structures)**: Stage depth is bounded ($\le 2$ levels).

### 3. Quality & Human Steering
- **Pattern 10 (Specs Are Contracts)**: Specs specify WHAT and WHEN (beat maps, moods, key moments), never prescribing HOW (code internals, pixel positions).
- **Pattern 11 (Checkpoints)**: Creative stages pause between steps (`| After Step | Agent Presents | Human Decides |`) for human redirection.
- **Pattern 12 (Stage Audits)**: Quality checklists (`| Check | Pass Condition |`) executed before saving to `output/`.
- **Pattern 13 (Value Validation)**: Output value types (e.g. TEACHES, PRACTICES, CHALLENGES) are locked before drafting.
- **Pattern 14 (Docs Over Outputs)**: Reference documentation is the sole ground truth. Agents never inspect previous outputs to learn conventions.
- **Pattern 15 (Shared Constants)**: Code workspaces centralize tokens/constants into single-source files.
