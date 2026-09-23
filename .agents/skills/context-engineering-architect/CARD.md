```ascii
┌──────────────────────────────────────────────────────────────────────┐
│ SKILL: context-engineering-architect                                 │
│ Category: agent_orchestration                                        │
│ Version: 1.0.0                                                       │
│ Invocation: /context-engineering-architect                           │
│ Triggers: "context engineering", "audit context", "fastmcp adapter", │
│           "subagent swarm topology", "nano harness", "agent hooks"   │
│ Requires: "agent-harness-architect", "crafting-skills"               │
│ Target: 6-layer context engineering stack & sandboxed ReAct loops    │
└──────────────────────────────────────────────────────────────────────┘
```

# Context Engineering Architect — Companion Summary Card

## Stage Progression Table

| Stage | Core Responsibility | Primary Artifact | Completion Gate |
|---|---|---|---|
| **Stage 1: Context Surface Audit** | Evaluate 6-layer stack completeness & token budget | `ContextStackScore` report | 6 layers scored, budget estimated |
| **Stage 2: Tool & Protocol Composition** | Compose FastMCP JSON-RPC tools & resource URIs | FastMCP server spec | Tool schemas & transports defined |
| **Stage 3: Subagent Partitioning** | Apply 10+ files heuristic to plan swarm topologies | `SubagentTopologyPlan` | Fan-Out/Pipeline/Supervisor planned |
| **Stage 4: Lifecycle Hook Synthesis** | Implement PreToolUse guardrails & live telemetry | Hook interceptor configuration | Fail-closed security rules active |
| **Stage 5: Autonomous Harness Loop** | Execute ReAct loop with safe_path sandboxing | `NanoHarnessTrajectory` | Confinement verified, settlement recorded |

---

## Key Invariants & Architectural Levers

- **6-Layer Stack Compliance**: Skills $\rightarrow$ FastMCP $\rightarrow$ Plugins $\rightarrow$ Subagents $\rightarrow$ Hooks $\rightarrow$ Loops.
- **The 10+ Files Rule**: Tasks spanning $\ge 10$ files must partition execution across subagents to prevent context blowout.
- **Path Confinement (`safe_path`)**: All filesystem operations must resolve within the active project workspace root.
- **Fail-Closed PreToolUse Hooks**: Security gates must default to denial on unknown command syntax or unparseable paths.
- **Bounded ReAct Step Safety**: Autonomous loops must enforce explicit step limits ($\le 30$) and catch tool exceptions gracefully.
- **Slotted/Frozen Domain Models (Rule 12)**: All report entities must use `@dataclass(slots=True, frozen=True)`.

---

## Mandatory Invariants Checklist

- [ ] **Progressive Disclosure**: Expose compact metadata in frontmatter, loading deep procedures only upon intent activation.
- [ ] **M×N Decoupling**: Isolate external tools behind FastMCP JSON-RPC servers rather than hardcoding vendor bindings.
- [ ] **Safe Path Confinement**: Assert `safe_path()` checks before executing any file write, edit, or shell execution.
- [ ] **Subagent Isolation**: Subagents must inherit isolated prompts and return structured settlement payloads.
- [ ] **Live Telemetry Non-Blocking**: Telemetry streams to external dashboards must never block agent reasoning steps.
