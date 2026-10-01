# Agent Reasoning & Execution Reference (`harness.agent`)

The `harness.agent` package provides the autonomous reasoning loops, step execution engines, session trees, and multi-agent swarm coordinators for Brain Harness.

---

## 1. `ReActAgentLoop` & `StepExecutionEngine`

### `ReActAgentLoop`
Primary implementation of `AgentLoopService` executing iterative ReAct reasoning cycles until task completion or step limit exhaustion.

#### Methods
- `run(task: str, session_id: str | None = None, max_steps: int = 25) -> AgentTaskResult`: Runs an autonomous agent task to completion.
- `step(session_id: str, prompt: str) -> AgentStep`: Executes a single interactive step within a session.

### `StepExecutionEngine`
Orchestrates single-step tool execution, in-flight codeblock parsing, and error self-repair.

#### Methods
- `execute_step(tool_call: ToolCall, context: ServiceContext) -> StepResult`: Executes a tool invocation inside an atomic context transaction.
- `normalize_stream(chunk_stream: AsyncIterator[str]) -> AsyncIterator[str]`: Auto-repairs trailing commas and unclosed JSON markdown fences in-flight before parsing.

---

## 2. `AgentSessionManager` & `AgentSession`

### `AgentSessionManager`
Manages branchable, persistent session trees tracking execution history and checkpoints.

#### Methods
- `create_session(task: str, parent_session_id: str | None = None) -> AgentSession`: Creates a new session node in the thread DAG (Rule 36).
- `get_session(session_id: str) -> AgentSession | None`: Retrieves an active or stored session.
- `complete_session(session_id: str, final_answer: str) -> None`: Marks a session completed.
- `fail_session(session_id: str, error_message: str) -> None`: Marks a session failed.
- `export_tree(session_id: str) -> str`: Renders an ASCII execution tree representation.
- `export_transcript(session_id: str) -> list[dict[str, Any]]`: Returns complete step transcript.

---

## 3. `SwarmCoordinator` & `SwarmDAG`

### `SwarmCoordinator`
Coordinates hierarchical multi-agent swarms across parallel waves and resolves collective decisions.

#### Methods
- `execute_swarm(dag: SwarmDAG, token_budget: int = 100000) -> SwarmTaskResult`: Executes swarm waves in topological order, monitoring token consumption via `TokenGovernor`.
- `deliberate_consensus(proposals: list[str], criteria: list[str]) -> str`: Resolves multi-agent debates via `ConsensusEngine` using Borda, weighted majority, or consensus voting.

### `SwarmNode`
A single execution node within a `SwarmDAG`.
- `node_id: str`: Unique node identifier.
- `task: str`: Instruction payload for the worker.
- `role: str`: Persona or specialized responsibility.
- `dependencies: list[str]`: Preceding node IDs required before execution.

---

## 4. `DefaultContextOptimizer` & `ContextOptimizationConfig`

### `DefaultContextOptimizer`
Applies deterministic pre-LLM context transformations to bound token consumption.

#### Methods
- `optimize_context(messages: list[dict[str, Any]], config: ContextOptimizationConfig) -> list[dict[str, Any]]`: Prunes redundant whitespace, middle-out truncates oversized tool outputs, and injects PageRanked AST repo maps.

### `ContextOptimizationConfig`
Configuration parameters for context pruning:
- `max_context_tokens: int`: Absolute token threshold before pruning triggers.
- `preserve_system_prompt: bool`: Guarantees system instructions are never truncated.
- `middle_out_threshold: int`: Token limit per tool output before middle-out reduction is applied.
