---
name: agent-harness-architect
description: Architect, evaluate, select, and sandbox production-grade AI agent harnesses and runtime loops using 5-part harness architecture, 4-mechanism validation, and 4-layer stack partitioning. Do not use for generic prompt writing or single-turn chat scripts.
---

# Agent Harness Architect: Runtime Shell & Selection Engine

`agent-harness-architect` is the cognitive and architectural engine for designing, auditing, selecting, and sandboxing production-grade AI agent runtime harnesses. Synthesized from Rudrendu Paul's foundational literature (*What Is an Agent Harness? The Architecture Behind Claude Code, DeepSeek Harness, and Hermes Agent*, freeCodeCamp, 2026), this skill operationalizes the shift from unopinionated agent framework libraries (2023–2025) to opinionated, turnkey agent harnesses (2026).

Rather than treating agent execution as an unbounded prompting loop, `agent-harness-architect` enforces the **5-Part Harness Architecture**, verifies the **4 Reliability Mechanisms** popularized by Claude Code and Deep Agents, decouples the **4-Layer Agent Stack** (MCP, Harness, Orchestration, Observability/Sandbox), and locks down load-bearing sandbox safety boundaries.

Every harness audit, design, or selection workflow executes this 5-stage progression:

```
[1. Failure Mode Bet Matching] → [2. 5-Part Harness Audit] → [3. 4-Mechanism Reliability Gate] → [4. 4-Layer Stack Auditing] → [5. Safety Invariants & Budget Gate]
```

See [CARD.md](CARD.md) for the companion summary card, stage matrix, and verification checklist.
Consult [../ai-agent-engineer/SKILL.md](../ai-agent-engineer/SKILL.md) for canonical agent architectural patterns, [../orca-orchestrator/SKILL.md](../orca-orchestrator/SKILL.md) for multi-worker Git worktree coordination, and [../crafting-skills/SKILL.md](../crafting-skills/SKILL.md) for skill authoring standards.

---

## 1. Failure Mode Diagnosis & Architectural Bet Matching

Diagnose the team's operational bottleneck and match it against the four competing architectural bets of 2026 harnesses:

1. **Diagnose Primary Operational Bottleneck**:
   - *Vendor / Model Lock-in*: Team needs to swap foundation models, tools, or sandboxes without rewriting orchestration logic.
   - *Unreliable Multi-Turn Execution*: Single-agent sessions drift off-task, hallucinate file states, or burn context by turn 25.
   - *Cross-Session Amnesia*: The agent re-reasons through identical domain workflows every morning from scratch.
   - *Audit Surface Bloat*: Security/compliance teams reject heavyweight runtimes with sprawling dependency trees.
2. **Select Architectural Bet**:
   - **Bet 1: Total Runtime Modularity (`deepseek-harness` / `dsh`)**:
     * Architecture as a configuration file. Every component—model provider, tool catalog, sandbox container, and terminal UI—is a swappable plugin managed by an IoC container (Cordis pattern).
   - **Bet 2: Fixed Mechanisms, Executed Reliably (`claude-code`, `deep-agents`, `aider`, `cline`)**:
     * Focus on four locked mechanisms (planning, sandboxed filesystem, subagents, context compression). Ideal for end-to-end coding loops where a reviewable diff or test pass is the unit of work.
   - **Bet 3: Compounding Memory & Omnichannel Presence (`hermes-agent`)**:
     * Persistent self-improvement. Successful multi-step solutions are committed to a shareable skill library. The agent operates as a standing assistant accessible via chat platforms (Slack, Discord, Telegram).
   - **Bet 4: Radical Minimalism (`pi`, `oh-my-pi`)**:
     * 4 built-in tools (`read_file`, `write_file`, `edit_file`, `run_bash`), radical transparency, and zero framework weight. Extended via typed extensions or Rust-based DAP/LSP engines (`omp`).
3. **Evaluate Adoption Curve Health**:
   - Distinguish launch spikes (e.g. 95,000 stars in 2 days) from compounding organic adoption (steady 1-year climb to 91,000+ stars). Prioritize maintainer commitment and sustained retention over vanity metrics.

> **Completion criterion**: Primary operational bottleneck diagnosed, target architectural bet justified, and baseline harness archetype selected.

---

## 2. Core 5-Part Harness Architecture Audit

Audit or scaffold the five architectural components that comprise every production runtime harness:

```
┌─────────────────────────────────────────────────────────────┐
│              CORE 5-PART HARNESS ARCHITECTURE               │
├──────────────────────────────┬──────────────────────────────┤
│ 1. Model Core                │ 2. Tool Router               │
│ - Unopinionated next-token / │ - Schema dispatch to local   │
│   tool-call prediction       │   filesystem, bash, or MCP   │
├──────────────────────────────┼──────────────────────────────┤
│ 3. Memory & Context Layer    │ 4. Pre-Execution Planning    │
│ - Context eviction, middle-  │ - Mandatory step commitments │
│   out compression, offload   │   before modifying state     │
├──────────────────────────────┴──────────────────────────────┤
│ 5. Sandbox Execution Boundary                               │
│ - Restricted filesystem jail, disposable micro-VMs (E2B)    │
└─────────────────────────────────────────────────────────────┘
```

1. **Verify the 5-Step Execution Loop**:
   - *Step 1 (Prompt Assembly)*: Harness compiles user intent, system instructions, and tool schemas.
   - *Step 2 (Model Prediction)*: Model emits reasoning and structured tool calls.
   - *Step 3 (Sandbox Tool Execution)*: Harness executes calls inside the sandbox and captures stdout/stderr.
   - *Step 4 (Context Append)*: Harness appends observations back into the message trajectory.
   - *Step 5 (Termination Evaluation)*: Harness evaluates stop conditions (final answer, max turns, cost limits, user interrupt).
2. **Audit Toy Loop Failure Seams**:
   - Inspect tool execution for unhandled exceptions that cause model spin.
   - Ensure the loop does not run bare `subprocess.run(shell=True)` directly on host working directories.

> **Completion criterion**: 5 core harness components verified and mapped; absence of unconstrained toy loops confirmed.

---

## 3. The 4-Mechanism Reliability Gate

Evaluate and enforce the four load-bearing mechanisms identified in Claude Code and LangChain Deep Agents:

1. **Mechanism A: Pre-Execution Planning Tool**:
   - Mandate that the model formulate and emit a structured execution plan before invoking file-mutating tools.
   - Enforce plan check-ins when execution deviates or exceeds estimated step bounds.
2. **Mechanism B: Virtual Filesystem & Isolated Sandbox**:
   - Confine all file reads, writes, and shell executions to an isolated path jail or disposable container.
   - Verify that relative path traversals (`../..`) cannot escape the sandbox boundary.
3. **Mechanism C: Subagent Delegation**:
   - Verify capability to spawn isolated sub-agents with dedicated, clean context windows.
   - Restrict sub-agents to specific bounded sub-tasks; return aggregated summaries to the parent context.
4. **Mechanism D: Context Compression & Memory Management**:
   - Implement middleware that monitors conversation token counts against window limits.
   - Offload large tool observation outputs (e.g. multi-megabyte log files) to storage pointers or apply middle-out compression.

### Diagnostic Reliability Scorecard

| Architectural Axis | Level 0: Toy / Fragile | Level 1: Intermediate | Level 2: Production Gate |
|---|---|---|---|
| **Planning Gate** | Direct execution on turn 1 | Ad-hoc textual plan request | Mandatory planning tool; approval gated |
| **Sandbox Isolation** | Bare host shell execution | Relative path checks (`cwd="./sandbox"`) | Ephemeral micro-VM (E2B/Modal) or Docker |
| **Subagent Delegation** | Monolithic single context | Inline simulated persona | Child agent spawned in isolated window |
| **Context Compression**| Raw dump into history | Hard message truncation | Middle-out compression & artifact pointers |
| **Observability** | Console print statements | Plain local log files | Distributed session tracing (Langfuse/LangSmith)|

> **Completion criterion**: Target harness audited against all 4 mechanisms; Level 2 production criteria satisfied on planning and sandboxing.

---

## 4. 4-Layer Stack Boundary Auditing

Audit architectural boundaries to ensure clean separation across the 4-layer agent stack:

```
┌─────────────────────────────────────────────────────────────┐
│                 THE 4-LAYER AGENT STACK                     │
├─────────────────────────────────────────────────────────────┤
│ Layer 4 (Cross-Cutting): Observability & Micro-VM Sandboxes │
│ - Tracing: Langfuse, LangSmith, Braintrust, Phoenix         │
│ - Sandboxing: E2B, Modal, Docker                            │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: Orchestration Frameworks                           │
│ - Multi-agent coordination graphs: LangGraph, CrewAI,       │
│   AG2, Mastra, DSPy                                         │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: Agent Harness Loop                                 │
│ - Opinionated single-agent ReAct shell: Claude Code, dsh,   │
│   Hermes Agent, Pi, Deep Agents                             │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: Protocol Standard (MCP)                            │
│ - Model Context Protocol tool servers & unified resources   │
└─────────────────────────────────────────────────────────────┘
```

1. **Verify Protocol Decoupling (Layer 1 - MCP)**:
   - Ensure tool integrations use declarative MCP server configurations rather than hardcoded client branches.
2. **Enforce Harness-Orchestration Boundary (Layer 2 vs Layer 3)**:
   - Do not force a single-agent harness loop to handle complex multi-persona DAG choreography.
   - Delegate stateful, long-running team workflows to Layer 3 orchestrators (LangGraph, Mastra).
3. **Attach Layer 4 Observability from Day One**:
   - Mandate session tracing (Langfuse, LangSmith) to capture per-turn token consumption, model latencies, and tool call payloads.
   - Eliminate unobservable failures at turn 30+ through detailed execution traces.

> **Completion criterion**: 4-layer boundaries verified; tools integrated via MCP; observability hooks wired.

---

## 5. Load-Bearing Safety Invariants & Hard Budget Enforcement

Enforce production runtime safeguards to prevent runaway execution, financial exhaustion, and filesystem corruption:

1. **Jail Path Containment Invariant**:
   - Tool execution paths must be pinned to explicit sandbox roots. Reject shell execution without verified directory confinement.
2. **Triple Budget Boundaries**:
   - *Turn Ceiling*: Configure non-optional `max_turns` (e.g. 15–30 turns) to prevent infinite ReAct loops.
   - *Financial / Token Budget*: Declare strict per-session token limits or USD expenditure ceilings.
   - *Wall-Clock Subprocess Timeout*: Enforce synchronous process execution timeouts (<= 120s) on all child bash commands.
3. **Defensive Error Recovery**:
   - Wrap tool dispatchers in defensive exception handlers. Capture exit codes, stdout, and stderr.
   - Provide informative diagnostic error messages to the model instead of crashing or returning empty payloads.

> **Completion criterion**: Hard turn limits, financial budgets, sandbox containment, and defensive error handlers actively enforced.

---

## The Visual Brief Specification

Before finalizing architectural recommendations or deploying new agent harnesses into production, the architect must generate an interactive HTML Visual Brief:

1. **Target Location**: Write the brief to `%TEMP%\agent-harness-<timestamp>.html` (or platform equivalent).
2. **Visual Brief Content**:
   - Dark theme (`#0d1117`) loading Tailwind CSS and Mermaid.js via CDN.
   - Render the **5-Stage Execution & Selection DAG** illustrating the decision flow across the 4 architectural bets.
   - Embed the **Diagnostic Reliability Scorecard Table** detailing Level 0 to Level 2 criteria.
   - Display the **Anti-Pattern Defense Matrix** with concrete mitigation rules.
3. **Delivery**: Present the clickable file URI to the user for visual inspection.

> **Completion criterion**: Visual brief generated in `%TEMP%`, verified non-empty, and presented as an active clickable link.

---

## Mandatory Checkpoint Gate

To prevent unreviewed harness migrations, insecure sandbox deployments, or runaway token loops:

1. **Checkpoint Artifact**: Author an `implementation_plan.md` artifact detailing:
   - Evaluated harness candidates and recommended architectural bet.
   - Sandbox security boundary specification and path jail configuration.
   - Hard budget bounds (`max_turns`, token limits, cost caps).
   - Tracing and observability backend configuration.
2. **Review Signal**: Set `RequestFeedback: true` in artifact metadata.
3. **Execution Gate**: **STOP and wait** for explicit human confirmation before deploying new harnesses or executing mutating commands.

> **Completion criterion**: Explicit human confirmation received at the Mandatory Checkpoint gate.

## Micro-Kernel IoC Integration & Headless CLI Dispatch

Per **AGENTS.md Rule 49**, `agent-harness-architect` is elevated from a passive prompt into an authoritative, slotted in-memory domain engine and typed IoC service:

1. **Micro-Kernel IoC Resolution**:
   ```python
   from harness.services.agent_harness import AGENT_HARNESS_ARCHITECT_SERVICE_KEY

   service = context.require(AGENT_HARNESS_ARCHITECT_SERVICE_KEY)
   report = service.audit(target_path=".")
   gate = service.evaluate_reliability()
   bet = service.classify_bet(bottleneck="vendor lock-in")
   brief_path = service.visual_brief(target_path=".")
   ```
2. **Headless Click CLI Commands**:
   - `harness architect audit [--target <dir>] [--json]` — 5-part architecture & 4-layer stack audit.
   - `harness architect score [--config <path>] [--json]` — 4-mechanism reliability scorecard (L0–L2).
   - `harness architect bet [--bottleneck <text>]` — Match operational bottleneck to 2026 harness bet.
   - `harness architect brief [--target <dir>] [--output <path>]` — Interactive HTML review report.
3. **Domain Engine & Plugin**:
   - Slotted domain engine: `scripts/agent_harness_architect.py` (`AgentHarnessArchitectEngine`)
   - Domain plugin: `plugins/agent_orchestration/agent_harness_architect/` (`plugin = AgentHarnessArchitectPlugin()`)

---

## Anti-Patterns

- **The Toy Loop Trap** — Deploying a bare 60-line loop using unconstrained subprocess execution without directory confinement, permission gating, or execution limits.
- **Unbounded Token Bleed** — Omitting max_turns or cost caps, allowing an autonomous agent to loop indefinitely and burn API budgets.
- **Silent Tool Error Death Spiral** — Failing to catch tool execution errors or malformed payloads, looping the model back into identical failing states.
- **Context Flooding Amnesia** — Inlining massive raw tool observations into conversation history without progressive compression or pointer offloading.
- **Premature Action Drift** — Allowing an agent to mutate code or infrastructure files before formulating and locking a structured execution plan.
- **Cross-Session Amnesia** — Forcing an agent to re-solve recurring procedural tasks from scratch on every run instead of indexing reusable skills.
- **Stack Layer Smearing** — Conflating single-agent runtime harness execution with multi-agent orchestration graphs or protocol connectivity.
