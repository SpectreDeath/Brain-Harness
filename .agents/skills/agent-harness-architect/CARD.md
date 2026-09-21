# Skill Summary Card: `agent-harness-architect`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:       agent-harness-architect                  │
│ Category:    agent_orchestration / runtime-harnesses   │
│ Invocation:  /agent-harness-architect                 │
│ Trigger:     "architect an agent harness",             │
│              "evaluate agent harness",                 │
│              "claude code vs deepseek harness",        │
│              "audit agent runtime loop",               │
│              "sandbox and planning gate",              │
│              "prevent agent context blowout",          │
│              "4-layer agent stack review"              │
│ Version:     1.0.0                                     │
│ Provides:    "agent_harness_architecture"              │
├────────────────────────────────────────────────────────┤
│ Target:      Architect, evaluate, select, and sandbox  │
│              production-grade AI agent harnesses using │
│              5-part architecture and 4 mechanisms.     │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Harness Engineering Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Bet Matching** | Match team bottleneck to one of four architectural bets | Bet Selection Matrix | Primary bottleneck diagnosed & bet selected |
| **2. 5-Part Audit** | Audit Model Core, Router, Memory, Planning, Sandbox | 5-Part Component Map | 5 core harness components verified |
| **3. 4-Mechanism Gate** | Verify Planning, Sandbox, Subagents, Context Compression | Reliability Scorecard | Level 2 production criteria satisfied |
| **4. 4-Layer Auditing** | Decouple MCP, Harness, Orchestration, Observability | Stack Boundary Blueprint | Clean 4-layer separation established |
| **5. Safety Invariants**| Enforce sandbox containment, turn bounds, error wraps | Hard Operational Policy | Triple budget & sandbox boundaries locked |

---

## The Three Pillars Cheat Sheet

### 1. The Core 5-Part Architecture & 4-Mechanism Gate
- **5 Parts**: Model Core + Tool Router + Memory/Context + Planning + Sandbox.
- **4 Reliability Mechanisms**:
  1. *Planning Tool*: Enforces structured step commitments before file mutations.
  2. *Virtual Filesystem*: Restricts operations to isolated paths or ephemeral containers.
  3. *Subagent Delegation*: Executes sub-tasks in clean context windows; reports summaries.
  4. *Context Compression*: Middle-out compression and observation pointer offloading.

### 2. The 4-Layer Agent Stack Decoupling
- **Layer 1 (Protocol)**: Model Context Protocol (MCP) for tool and resource standardized connections.
- **Layer 2 (Harness Loop)**: Single-agent ReAct runtime shell (`claude-code`, `dsh`, `pi`, `hermes`).
- **Layer 3 (Orchestration)**: Multi-agent coordination graphs (`LangGraph`, `CrewAI`, `Mastra`).
- **Layer 4 (Observability & Sandbox)**: Tracing (`Langfuse`, `LangSmith`) + Disposable micro-VMs (`E2B`, `Modal`).

### 3. Load-Bearing Safety Invariants
- **Directory Confinement**: Non-deletable sandbox `cwd` root boundary.
- **Triple Budget Gate**: Explicit `max_turns` (15–30), financial USD cap, and process timeouts.
- **Defensive Error Wrappers**: Catch all tool exceptions to prevent infinite model error loops.

---

## Verification & Quality Checklist

- [ ] **Positive Phrasing**: Instructions define affirmative engineering rules rather than vague prohibitions.
- [ ] **Domain Vocabulary**: Employs rigorous architectural concepts (*harness*, *runtime shell*, *MCP*, *sandbox jail*, *subagent delegation*, *middle-out compression*).
- [ ] **Exhaustive Completion Criteria**: Every stage specifies unambiguous verification gates.
- [ ] **Companion Card Present**: Co-located `CARD.md` authored with single-pipe `│` borders and `SKILL:` tag.
- [ ] **Zero-Fork Configuration**: Co-located `config.default.yaml` defining baseline operational budgets.
- [ ] **Pre-Flight Validation**: Passes `python -m harness.cli skills validate` with zero warnings.
