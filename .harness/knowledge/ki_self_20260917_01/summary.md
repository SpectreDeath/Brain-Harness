# Knowledge Item: Five-Part Agent Harness Architecture and Four-Mechanism Reliability Invariant

## Epistemic Distillation

### 1. Paradigm Shift: From Frameworks to Harnesses
Between 2023 and 2025, the AI agent ecosystem was characterized by unopinionated agent framework libraries (LangChain, AutoGen, CrewAI). Developers assembled component building blocks, authored custom model calls, and wired custom tool routing. 

By 2026, the paradigm shifted decisively toward **Agent Harnesses** (Claude Code, DeepSeek Harness, Hermes Agent, Pi). An agent harness is an opinionated runtime shell wrapped around a foundation model. While the model core only predicts the next token or tool call, the harness executes the 5-step loop, isolates tool execution, compresses memory over dozens of turns, and coordinates subagents.

### 2. The Core Five-Part Architecture & Five-Step Loop
Every production agent harness implements five essential components:
1. **Model Core**: Predicts next messages and tool invocations.
2. **Tool Router**: Dispatches tool invocations to local sandboxes, host processes, or external MCP servers.
3. **Memory Layer**: Governs context retention, history compression, and observation eviction across turns.
4. **Planning Layer**: Decomposes complex tasks into discrete steps before modifying filesystem state.
5. **Sandbox Boundary**: Enforces execution containment, preventing unapproved host filesystem mutations.

The standard execution loop executes five sequential steps:
`Prompt Assembly` $ightarrow$ `Model Prediction` $ightarrow$ `Sandbox Tool Execution` $ightarrow$ `Context Observation Append` $ightarrow$ `Termination Evaluation`.

### 3. The Four Reliability Mechanisms
As reverse-engineered by LangChain's Deep Agents from Claude Code, reliable multi-turn execution depends on four critical mechanisms:
- **Planning Tool**: Compels the model to write out structured steps before touching files, eliminating silent task drift over long sessions.
- **Virtual Filesystem & Sandbox**: Constrains read/write/execute operations to isolated directories or ephemeral micro-VMs (e.g. E2B, Modal).
- **Subagent Delegation**: Spawns isolated child agents with independent context windows for focused sub-tasks, returning distilled summaries to prevent context pollution.
- **Context Compression Middleware**: Automatically compresses past conversation history and offloads large tool observations (50KB+) to storage pointers.

### 4. Four Competing Architectural Bets
The 2026 agent landscape is defined by four distinct architectural philosophies:
- **Bet 1: Total Runtime Modularity (`deepseek-harness` / `dsh`)**: Architecture as configuration; every subsystem (model, tool, sandbox, UI) is a swappable plugin in an IoC container.
- **Bet 2: Fixed Mechanisms, Executed Well (`claude-code`, `deep-agents`, `aider`, `cline`)**: Focus on planning, sandboxing, subagents, and compression for end-to-end coding tasks with verifiable diffs.
- **Bet 3: Compounding Memory (`hermes-agent`)**: Inter-session skill accumulation; solving non-trivial tasks saves reusable procedural skills for future recall across chat channels.
- **Bet 4: Radical Minimalism (`pi`, `oh-my-pi`)**: Radical simplicity (4 built-in tools) with zero bloat; organic developer adoption backed by typed extensions or Rust-native LSP engines.

### 5. The Four-Layer Solution Stack
Production deployments decouple into four horizontal layers:
1. **Protocol Layer (MCP)**: Universal standard for connecting models to external tools and resources.
2. **Harness Loop Layer**: Turnkey single-agent ReAct runtime shell.
3. **Orchestration Layer**: Multi-agent graph coordination (LangGraph, CrewAI, AG2, Mastra).
4. **Cross-Cutting Observability & Sandboxing**: Session tracing (Langfuse, LangSmith, Braintrust) and isolated micro-VM execution (E2B, Modal).

### 6. Load-Bearing Safety Invariants
- **Sandbox Root Jail**: The execution directory (`cwd`) must remain strictly confined; bare `subprocess.run(shell=True)` without path confinement is an unacceptable security vulnerability.
- **Triple Budget Ceilings**: Mandatory `max_turns` limits, financial USD caps, and subprocess timeouts prevent runaway loops and token exhaustion.
- **Defensive Tool Exception Handling**: Malformed tool calls must be caught and structured as diagnostic observations rather than crashing the harness or looping infinitely.
