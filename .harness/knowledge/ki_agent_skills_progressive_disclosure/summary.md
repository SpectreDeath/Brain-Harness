# Agent Skills Progressive Disclosure & Loose Constraint Architecture

**ID:** `ki_agent_skills_progressive_disclosure`  
**Category:** `agent_orchestration`  
**Origin:** Daniel Warfield (*Agent Skills — Intuitively and Exhaustively Explained*, IAEE) & Sergey Menshykh (*Agent Skills Open Specification*, agentskills.io / Microsoft Learn)  
**Provenance Lineage:** Published September 2026.

## Executive Summary
Agent Skills represent an open standard bridging the divide between "unconstrained" agents (pure ReAct loops prone to stochastic drift and repetitive mistakes) and "constrained" agents (rigid, monolithic state graphs like LangGraph that are brittle to author and maintain). By providing modular, on-demand "portable plans" and "loose constraints", skills enforce local operational rules without sacrificing autonomous reasoning.

Crucially, skills resolve the **Context Flooding Dilemma** through the **Three-Tier Progressive Disclosure Pattern**, allowing agents to browse dozens of skills at zero token overhead until a capability is dynamically invoked.

---

## Core Mental Models

### 1. The Constrained vs. Unconstrained Spectrum
- **Unconstrained Agents (ReAct / Claude Code)**:
  - *Strengths*: Highly flexible, adaptive to novel circumstances, minimal authoring overhead.
  - *Weaknesses*: Stochastic drift, context exhaustion, repeat errors across trajectories.
- **Constrained Agents (State Graphs / Workflows)**:
  - *Strengths*: Deterministic step guarantees, hard state bounds.
  - *Weaknesses*: Extreme brittleness, high maintenance overhead, unable to adapt when an edge fails.
- **Agent Skills as the Bridge ("Portable Plans")**:
  - Skills inject declarative domain expertise, step-by-step procedures, and guardrails directly into the agent's turn.
  - The agent remains autonomous in execution while bound by local negative boundaries and explicit completion criteria.

### 2. The 3-Tier Progressive Disclosure Architecture
```
┌─────────────────────────────────────────────────────────────┐
│ Tier 1: Discovery Catalog (~50 tokens per skill)            │
│ Injected into System Prompt / Tool List                     │
│ [name, short description, activation triggers]              │
└──────────────────────────────┬──────────────────────────────┘
                               │ Agent determines relevance (load_skill)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Tier 2: Instruction Body (< 500 lines)                      │
│ Loaded into Working Context on-demand                       │
│ [SKILL.md: 5-stage loop, completion criteria, anti-patterns]│
└──────────────────────────────┬──────────────────────────────┘
                               │ Agent selectively queries resources / scripts
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Tier 3: Execution on Demand (Zero initial context)          │
│ Read / Executed only when actively needed                   │
│ [resources/*.csv, schemas, scripts/*.py, remote MCP endpoints]
└─────────────────────────────────────────────────────────────┘
```

---

## Architectural Invariants
1. **Zero-Overhead Discovery Invariant**: Tier 1 metadata must never exceed 200 characters per skill description to protect baseline system prompt token budgets.
2. **Context Offloading Invariant**: Any tabular conversion data, JSON schemas, or auxiliary documentation exceeding 50 lines must be placed in `resources/` (Tier 3) rather than inlined in `SKILL.md` (Tier 2).
3. **Turn-Level Fault Isolation**: If an operation within a skill fails, the failure is isolated to that agent turn; it does not corrupt cross-turn session state.
