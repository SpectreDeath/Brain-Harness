# Codebase Context Governance Playbook

## 1. The Three-Layer Context Taxonomy
AI coding agents perform best when context is strictly stratified by altitude:

| Layer | Name | Scope | Location | Update Frequency |
|---|---|---|---|---|
| **Layer 1** | Constitution & Kernel | Security, Invariants, Core Rules | Kernel / System Prompt | Rarely (Architect Review) |
| **Layer 2** | Project Execution (SSOT) | Tool commands, test suites, module seams | `AGENTS.md`, `CLAUDE.md` | Bi-weekly / Sprint |
| **Layer 3** | Ephemeral Task Context | Session history, scratch files, subtasks | Task memory / Transcripts | Per interaction |

## 2. Smell Diagnostics & Remedies
- **Smell: Lint Leakage**:
  - *Symptom*: Agent config file contains 50 lines of compiler errors or flake8 logs.
  - *Remedy*: Move diagnostics to ephemeral test logs; keep instruction files declarative.
- **Smell: Generic Tutorials**:
  - *Symptom*: Teaching the agent what pytest or git is.
  - *Remedy*: Delete generic prose; LLMs already know standard libraries. Focus exclusively on repo-specific seams.
- **Smell: Multi-Master Drift**:
  - *Symptom*: `CLAUDE.md` has rules not present in `AGENTS.md`.
  - *Remedy*: Designate `AGENTS.md` as primary and generate client variants via automated sync.
