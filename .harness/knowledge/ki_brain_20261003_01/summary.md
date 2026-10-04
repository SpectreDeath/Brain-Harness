# Antigravity IDE Brain Workspace Epistemic Topology and Scratch Salvage Invariants

## Problem
In IDE-integrated agentic development, autonomous agents construct an expansive filesystem-native workspace store under `C:\Users\spectre\.gemini\antigravity-ide\brain\`. Across 343 conversation directories, this store accumulates:
1. **1,085 Python scratch tools** (`brain/<cid>/scratch/`) authored on-the-fly for AST linting, schema reflection, test verification, and visual brief generation.
2. **530 strategic documents** (264 `implementation_plan.md` and 266 `walkthrough.md`) tracking intent-to-implementation divergence.
3. **1,655 subprocess task execution logs** (`.system_generated/tasks/task-*.log`) recording background process completions, pipe buffer exhaustion, and non-zero exit codes.
4. **243 paired dual-transcript streams** (`transcript.jsonl` compact vs `transcript_full.jsonl` untruncated).

Standard retrieval approaches fail against this store: recursive unpruned scans trigger pipe exhaustion and CPU spin (Rule 52), direct reads hit IDE system protection boundaries (Rule 46), sequential string scanning on transcripts exhausts memory (Rule 48), and compact transcript parsing misses truncated reasoning tokens.

## Solution
The `brain-artifact-miner` architecture establishes a comprehensive 5-stage workspace archaeology pipeline:

1. **Boundary-Resilient Handshake (Rule 46)**:
   - Evaluates target session paths with UTF-8 configured standard streams (`reconfigure(encoding='utf-8')`, Rule 23, Rule 50).
   - Pivots immediately to non-modifying shell reads (`Get-Content`, `Get-ChildItem`) or decoupled relational SQLite databases (`conversations/<cid>.db`) whenever IDE security boundaries block direct filesystem inspection.

2. **$O(1)$ Binary Byte-Offset Indexing & Dual Linking (Rule 22, Rule 48)**:
   - Compiles binary byte-offset seek tables (`open(..., 'rb')`) mapping step indices to file pointer ranges, guaranteeing $O(1)$ sub-millisecond retrieval without memory overhead.
   - Synchronizes dual transcripts: detects `is_truncated: true` in compact streams and automatically dereferences to `transcript_full.jsonl` at matching `step_index` to recover untruncated model thoughts and raw tool payloads.

3. **AST Scratch Tool Archaeology & Subprocess Task Triage (Rules 32, 42, 51, 53)**:
   - Classifies 1,085 scratch tools across 7 functional domain archetypes using Python `ast.parse` and `ast.walk`.
   - Strictly enforces defensive batch visibility: logs unexpected exceptions at `logger.warning()` and reraises `NameError`, `TypeError`, and `AttributeError` loudly to eliminate silent classification corruption (Rule 32).
   - Triages 1,655 background task logs via bounded ring buffers to surface exit codes and pipe deadlock diagnostics (Rule 53).
   - Generates standalone visual briefs with double-brace escaped CSS/regex templates (`{{`, `}}`, Rule 51).

4. **Dual-Lens Cognitive Bifurcation (Rule 40, Rule 41)**:
   - Epistemic invariants and verified decision lineages are committed to the Knowledge Vault under canonical dual-file directory layouts (`metadata.json` + `summary.md`).
   - Procedural capabilities are scaffolded into executable skills with companion cards (`CARD.md`) and zero-fork baseline budgets (`config.default.yaml`).

## Provenance
- Architectural Rules: `AGENTS.md` (Rules 12, 22, 23, 26, 32, 33, 37, 40, 41, 44, 46, 47, 48, 50, 51, 52, 53, 57).
- Primary Implementation: `.agents/skills/brain-artifact-miner/scripts/brain_artifact_miner.py`.
- Empirical Verification: Deconstructive census across 343 conversation workspaces and 139.9 MB of brain store artifacts at `C:\Users\spectre\.gemini\antigravity-ide\brain\`.
