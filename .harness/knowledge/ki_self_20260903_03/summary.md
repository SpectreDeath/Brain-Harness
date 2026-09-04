# Epistemic Memory Promotion Pipeline & Held-Out Judge Invariant

**ID:** `ki_self_20260903_03`  
**Category:** `memory_and_epistemics`  
**Origin:** `Brain Harness Execution History`  
**Provenance Lineage:** `skills discussion.md`, `.agents/skills/epistemic-memory-lifecycle/SKILL.md`, `book-to-skill-forge-20260903_174549.html`

## Executive Summary
Autonomous agents that write directly to long-term memory or self-promote candidate heuristics suffer from confirmation bias and self-confirming agentic drift. The epistemic memory lifecycle partitions memory into 6 discrete classes (Episodic, Semantic, Procedural, Constitutional Non-Learning Core, Theory of Mind, Prospective) and transitions knowledge items through an 8-state promotion machine (`CANDIDATE` -> `TRIAGED` -> `ANALYZED` -> `CONSOLIDATED` -> `EVALUATED` -> `PROMOTED` / `QUARANTINED` / `DEPRECATED`). Crucially, promotion requires validation by an isolated held-out judge model.

## Architectural Invariants & Rules
1. **Constitutional Non-Learning Core Protection:** Safety invariants, root identity, and ethical constraints are immutable and barred from automated promotional backpropagation.
2. **Theory of Mind Separation:** Agent state, user beliefs, and external ground-truth facts must remain partitioned. Never mutate a user profile based on speculative tool observations.
3. **Held-Out Model Evaluation Gate:** An agent cannot evaluate its own candidate memories for final promotion. Candidate memories must be scored by an independent judge model against held-out regression benchmark tasks.
4. **Authorial Continuity (Theseus Audit):** Verify the 4 pillars (Structural, Behavioral, Epistemic, Functional) before any memory mutation.
5. **Bounded Refinement Ceiling:** Internal reflection loops must be bounded to $\le 10$ steps with early convergence termination.
