---
name: context-engineering-architect
description: Architect, audit, compose, and govern autonomous code agent context using the 6-layer stack (skills, FastMCP, plugins, subagents, hooks, nano harness) and path confinement. Do not use for generic single-turn prompt crafting or non-agent chat writing.
---

# Context Engineering Architect: The 6-Layer Code Agent Context Engine

`context-engineering-architect` is the unified engineering engine for designing, auditing, and executing autonomous code agent context systems. Grounded in the Hugging Face *Context Course: Context Engineering for Code Agents* (Ben Burtenshaw et al., 2026), it elevates agent development from naive prompt manipulation to a rigorous, systems-level context discipline.

Every context engineering cycle operates across the 6-layer stack:
```
[1. Skills] ──► [2. FastMCP] ──► [3. Plugins] ──► [4. Subagents] ──► [5. Hooks] ──► [6. Nano Harness]
```

See [CARD.md](CARD.md) for the companion summary card, stage progression table, and invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline operational budgets and timeout thresholds.
Consult `../agent-harness-architect/SKILL.md` for runtime loop architectures and `../crafting-skills/SKILL.md` for skill authoring standards.

---

## The 5-Stage Context Engineering Progression

```
[1. Context Surface & Budget Audit]
              │
              ▼
[2. Tool & Protocol Composition (FastMCP)]
              │
              ▼
[3. Subagent & Swarm Partitioning (10+ Files)]
              │
              ▼
[4. Lifecycle Hook & Guardrail Synthesis]
              │
              ▼
[5. Autonomous Harness Loop & Sandboxed Execution]
```

---

## 1. Context Surface & Budget Audit (Shu)

Assess project workspace context completeness and bound per-turn token budgets:

1. **Evaluate the 6-Layer Context Stack**:
   - Inspect workspace for portable skills (`.agents/skills/`, `skills/`), MCP servers (`mcp_config.json`), manifest plugins (`plugin.json`), subagent guides, lifecycle hooks, and harness loops.
   - Run `ContextEngineeringEngine.audit_context_surface(project_dir)` to compute `ContextStackScore`.
2. **Bound Token Economics**:
   - Classify context state: `OPTIMIZED` (3,500 tokens), `PARTIAL` (8,000 tokens), `BLOATED` (15,000 tokens), or `MINIMAL` (25,000 tokens).
   - Formulate actionable remediation steps for missing layers.

> **Completion criterion**: 6 layers evaluated, `ContextStackScore` formulated, and token budget ceiling established.

---

## 2. Tool & Protocol Composition (FastMCP) (Shu)

Decouple tools, dynamic resources, and prompt templates behind Model Context Protocol (MCP) servers:

1. **Universal Adapter Modeling**:
   - Replace direct hardcoded tool imports with FastMCP JSON-RPC servers.
   - Define callable `@mcp.tool()` endpoints with strict Python type annotations and Google-style docstrings for schema synthesis.
2. **Transport Selection**:
   - Use **stdio** transport for local sandboxed CLI scripts and file operations.
   - Use **SSE / HTTP** transport for distributed services and Gradio Spaces integrations.

> **Completion criterion**: FastMCP server defined, tools typed, and transport mechanism configured.

---

## 3. Subagent & Swarm Partitioning (Ha)

Apply empirical context boundaries to partition large tasks across isolated subagents:

1. **Enforce the 10+ Files Rule**:
   - When a task touches, inspects, or edits $\ge 10$ files, reject single-agent execution to prevent context window blowout.
   - Run `ContextEngineeringEngine.plan_subagent_topology(files_count, task_type)` to determine the optimal pattern:
     - **Fan-Out / Fan-In**: For multi-module reviews, security audits, and parallel file lints.
     - **Pipeline**: For multi-stage refactoring (Spec $\rightarrow$ Implementation $\rightarrow$ Verification).
     - **Supervisor**: For broad exploratory tasks requiring dynamic delegation.
2. **Context Window Isolation**:
   - Subagents must inherit minimal scoped prompts, returning structured summary settlements to the parent orchestrator.

> **Completion criterion**: Subagent coordination topology selected with verified context savings estimates.

---

## 4. Lifecycle Hook & Guardrail Synthesis (Ha)

Establish programmatic runtime boundaries that models cannot hallucinate past:

1. **PreToolUse Security Interception**:
   - Intercept tool calls prior to execution.
   - Enforce fail-closed permission gates: return `"allow"`, `"deny"` (with diagnostic reason for in-flight self-repair), or `"modify"`.
2. **PostToolUse & Live Telemetry**:
   - Truncate oversized command outputs middle-out.
   - Stream structured execution events out-of-band to a local Gradio telemetry dashboard with a strict $\le 200\text{ms}$ timeout.

> **Completion criterion**: PreToolUse and PostToolUse hook interceptors configured with non-blocking telemetry.

---

## 5. Autonomous Harness Loop & Sandboxed Execution (Ri)

Execute minimal, robust ReAct loops governed by filesystem path confinement:

1. **Filesystem Path Confinement (`safe_path`)**:
   - Assert all file operations resolve strictly within the active workspace root (`safe_path(target, root)`).
   - Reject relative traversal escapes (`../../`) with `PermissionError`.
2. **Bounded ReAct Step Execution**:
   - Enforce step limits ($\le 30$) to prevent infinite loops.
   - Catch tool exceptions gracefully, returning diagnostic error observations for in-flight self-repair before final settlement.

> **Completion criterion**: ReAct loop executed to terminal settlement with 100% path confinement verified.

---

## The Three Foundational Pillars

### 1. The 6-Layer Progressive Context Staging Pillar
Never dump uncurated manuals or entire repositories into prompt context. Expose compact frontmatter catalogs (Tier 1), loading detailed skill instructions (Tier 2) and dynamic FastMCP tools (Tier 3) only when explicitly triggered.

### 2. Deterministic Sandboxing & Safe Paths
LLMs cannot be trusted to self-enforce path boundaries. All agent file modifications and tool executions must execute inside deterministic `safe_path` wrappers that verify paths against workspace roots.

### 3. Active Observability & Telemetry
Decouple agent reasoning from monitoring. Use asynchronous lifecycle hooks to stream execution trajectories to external Gradio dashboards without adding latency to the model reasoning loop.

---

## Anti-Patterns

- **Context Window Bloat** — Ingesting dozens of raw files into the main agent context instead of partitioning tasks across subagents via the 10+ files rule.
- **Unconfined File Operations** — Writing or modifying files using unverified relative paths without `safe_path()` workspace root assertions.
- **Hardcoded Tool Tight-Coupling** — Binding tools directly to specific agent runtimes instead of exposing them via the universal FastMCP JSON-RPC protocol.
- **Blocking Telemetry Latency** — Hooking synchronous network logging into the agent step loop that stalls reasoning when monitoring services lag.
- **Prompt-Based Security Illusion** — Relying on system prompt instructions like "do not delete files" instead of programmatic `PreToolUse` hook denial gates.
- **Unbounded Loop Execution** — Running ReAct agent loops without an explicit step limit counter, risking infinite API billing loops.
