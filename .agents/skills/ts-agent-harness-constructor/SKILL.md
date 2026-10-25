---
name: ts-agent-harness-constructor
description: Construct, validate, and harden zero-dependency AI agent runtime harnesses in TypeScript/Node.js: provider-agnostic loop, contract registry, workspace jail, atomic batch budgets, context windowing, and seeded failure testing. Do not use for harness selection, framework wrappers, or prompt-only scripts.
version: 1.0.0
category: agent_orchestration
tags:
  - typescript
  - agent_harness
  - runtime_loop
  - workspace_confinement
  - tool_validation
  - context_windowing
  - failure_testing
provides:
  - typescript_agent_harness_construction
  - tool_contract_registry
  - workspace_confinement_pattern
  - agent_failure_testing
requires: []
---

# TypeScript Agent Harness Constructor (`ts-agent-harness-constructor`)

## Scope & Architectural Seam

This skill provides an authoritative, zero-dependency engineering standard for constructing, validating, and hardening autonomous AI agent runtime harnesses in TypeScript and Node.js. It focuses on the core runtime mechanics: the ReAct agent loop, tool contract validation, filesystem sandboxing, command execution hardening, atomic batch budgeting, sliding context windowing, non-invasive telemetry, and seeded failure testing.

> [!IMPORTANT]
> **Cross-Reference Seam**: For harness architecture selection, 5-part comparative evaluation, and sandboxing governance, invoke upstream [agent-harness-architect](../agent-harness-architect/SKILL.md). Use `ts-agent-harness-constructor` strictly for **implementation, construction, and hardening** from first principles.

---

## Interactive Visual Brief

> Note: the interactive visual brief for this workflow was rendered to a local temp file at generation time and is not shipped with the skill, so the original link (which pointed at a `file:///` temp path) has been removed. The brief covered animated ReAct turn transitions, symlink walk diagrams, atomic batch budget timelines, and context window sliding group animations.

---

## The 6-Stage Operational Progression ("Shu" Stage)

Harness construction follows a strict 6-stage linear progression where each stage introduces a distinct architectural boundary and failure mode isolation:

```
[1. Loop & Model Abstraction] ➔ [2. Contract Registry & Validation] ➔ [3. Workspace Containment & Presets]
               ➔ [4. Execution Limits & Cancellation] ➔ [5. Atomic Context Windowing] ➔ [6. Telemetry, Evals & Adapters]
```

### Stage 1: Provider-Agnostic Loop & Model Abstraction

The core agent loop coordinates conversation state, dispatches model generations, routes tool calls, and handles cancellation.

1. **Harness Entrypoint**: Implement `runAgent({ prompt, model, tools, signal, maxSteps })` as the single public entrypoint returning an immutable execution summary:
   ```typescript
   export interface RunResult {
     status: 'completed' | 'step_limit' | 'tool_limit' | 'aborted' | 'model_error';
     answer?: string;
     messages: Message[];
     steps: number;
     usage: UsageTotals;
   }
   ```
2. **Model Provider Interface**: Decouple the LLM provider behind a minimal contract:
   ```typescript
   export interface Model {
     generate(params: {
       messages: Message[];
       tools?: ToolDefinition[];
       signal?: AbortSignal;
     }): Promise<ModelResponse>;
   }
   ```
3. **Scripted Test Harness**: Construct `scriptedModel(responses[])` to advance through predetermined responses in unit tests. It must throw `'Scripted model exhausted'` if the loop requests unexpected turns, ensuring complete test determinism without live API calls.
4. **Completion Gate**: Basic loop unit tests pass with `scriptedModel` covering: single-turn answers, tool invocation and result feedback, unknown tool handling, step limit termination, and `AbortSignal` cancellation.

### Stage 2: Contract Registry & Runtime Argument Validation

LLM model outputs are inherently untrusted. Never pass unvalidated arguments to tool implementations.

1. **ToolRegistry Contract**: Implement `ToolRegistry` enforcing tool name regex `^[a-zA-Z][a-zA-Z0-9_-]*$` and duplicate registration rejection.
2. **Pre-Dispatch Schema Validation**: Validate arguments against the tool's JSON Schema before dispatching to `execute()`:
   - Support JSON Schema subset: `type`, `properties`, `required`, `additionalProperties: false`, `items`, `enum`.
   - Report exact failure paths (e.g., `$.flags[0]` or `$.path: required`).
3. **Strict Error Bifurcation**:
   - **Tool Failure (Recoverable)**: Unknown tool name, schema validation failure, or exception thrown inside `tool.execute()` ➔ synthesize a `role: 'tool'` message with `isError: true`. The model observes the error and can self-repair on the next turn.
   - **Model Failure (Terminal)**: `model.generate()` throws (network crash, authentication failure, quota exhaustion) ➔ terminate immediately with `status: 'model_error'`. Never inject synthetic model recovery into the conversation for infrastructure failures.
4. **Completion Gate**: Malformed model-generated arguments never reach `tool.execute()`; model network crashes yield `model_error`; dedicated test cases verify both paths are strictly non-interchangeable.

### Stage 3: Workspace Containment & Hardened Command Presets

Agents must not read or modify files outside their designated project sandbox or execute arbitrary shell commands.

1. **Workspace Root Canonicalization**: Resolve root path using `await realpath(root)` to prevent base directory symlink deception.
2. **Path Confinement & Ancestor Walk**:
   - Enforce lexical containment via `path.resolve(root, input)` and `path.relative(root, resolved)`. Reject absolute paths and `..` escape attempts.
   - Perform a component-by-component `lstat()` walk on **every ancestor directory** up to root. Reject the operation if any parent directory is a symbolic link.
   - Use `O_NOFOLLOW` flag when opening files to prevent symlink race conditions (TOCTOU).
3. **Hardened Command Execution Presets**:
   - Disallow raw shell command strings (`exec("rm -rf " + input)`).
   - Require developers to declare explicit presets:
     ```typescript
     export interface CommandPreset {
       name: string;
       executable: string;
       args: string[];
       timeoutMs: number;
     }
     ```
   - The model selects presets by `name` only; it cannot supply executables, add arguments, or invoke shell pipelines.
   - Spawn child processes with `shell: false`, enforce timeout termination (`child.kill('SIGTERM')`), and cap both `stdout` and `stderr` buffers to 64 KB to prevent memory exhaustion.
4. **Completion Gate**: Traversal attempts (`../../etc/passwd`), symlinked ancestor escapes, and unlisted command names return recoverable tool errors; `shell: false` is verified by test; buffer overflow caps are asserted.

### Stage 4: Execution Limits & Cancellation Propagation

Agent runs must have bounded operational budgets and respond immediately to external cancellation.

1. **Decoupled Budget Limits**:
   - `maxSteps`: Maximum model conversation turns (default: 25).
   - `maxToolCalls`: Cumulative individual tool invocations across the entire run (default: 75), including failed or rejected calls.
2. **Atomic Batch Budget Verification**:
   - When a model emits multiple tool calls in a single turn, calculate:
     `remaining = maxToolCalls - cumulativeCalls`
   - If `calls.length > remaining`, **reject the entire batch atomically before mutating the conversation transcript**.
   - Terminate the run immediately with `status: 'tool_limit'`. Do NOT append the assistant message or execute a partial prefix of the batch. This prevents orphaned, unanswered tool calls in the transcript.
3. **AbortSignal Propagation**:
   - Thread `signal` through `model.generate({ signal })`, `tool.execute(args, signal)`, and `child_process.spawn({ signal })`.
   - Check `signal.aborted` at loop entry and immediately following every awaited asynchronous operation.
4. **Completion Gate**: Seeded PRNG property tests (`seed: 0x12345678`, 150 iterations varying `limit ∈ [0, 8]` and `batch ∈ [0, 12]`) verify that admitted batches execute all calls, rejected batches execute zero calls, and rejected batches leave no orphaned tool calls in the transcript.

### Stage 5: Atomic Context Windowing

As conversations grow, histories must be pruned to fit model context limits without breaking conversation integrity.

1. **Context Slicing Function**: Implement `selectContext(messages, maxChars)` with strict `RangeError` guards on non-positive character budgets.
2. **Indivisible Turn Groups**:
   - Never split an assistant tool-call turn from its corresponding tool result messages.
   - Group messages into atomic units: `[UserPrompt]`, `[AssistantTurn + ToolResults...]`, `[AssistantFinalAnswer]`.
   - Sliding windowing accumulates whole groups walking backward from the most recent turn.
3. **Transcript Integrity Invariants**:
   - Detect and throw on: orphaned tool results (tool message without preceding assistant call), duplicate tool-call IDs within a turn, or incomplete batches (tool result IDs mismatching assistant calls).
   - The initial user prompt must always be preserved.
   - If the initial prompt plus the most recent required group exceeds `maxChars`, terminate with `context_limit`.
4. **Completion Gate**: Tests verify batch indivisibility is preserved under aggressive character constraints, orphan tool results are detected and rejected, tool outputs are truncated before windowing, and coherent message transcripts are emitted regardless of conversation length.

### Stage 6: Non-Invasive Telemetry, Evals & Provider Adapter Pattern

Operational visibility and model connectivity must not invade or destabilize core loop mechanics.

1. **Boundary Event Stream**:
   - Emit typed lifecycle events via optional `onEvent` callback: `model_start`, `model_end` (with `durationMs`), `tool_start`, `tool_end` (with `durationMs`), `model_error`, `run_end`.
   - Each event carries monotonic `sequence`, unique `runId`, and ISO `timestamp`.
2. **Observer Isolation Invariant**:
   - Wrap all `onEvent?.(event)` dispatches in isolated `try...catch` blocks.
   - Route listener exceptions to optional `onObserverError`; suppress errors if no handler exists.
   - **Critical Rule**: An exception in a metrics logger, console formatter, or telemetry client must NEVER fail or alter the outcome of an agent run.
3. **Accurate Token & Cost Telemetry**:
   - Accumulate `usage.inputTokens`, `usage.outputTokens`, and `usage.modelCallsWithUsage`.
   - Distinguish `modelCallsWithUsage === 0` (cost unknown / provider omitted tokens) from `inputTokens === 0` (zero-cost run).
   - Validate usage values: reject negative numbers or non-integers with `RangeError`.
4. **Provider Adapter Coaching Note**:
   - Real LLM providers connect strictly via the `Model` interface: `generate({ messages, tools, signal }) → Promise<ModelResponse>`.
   - Adapters must:
     1. Translate between provider message formats (OpenAI, Anthropic, Gemini) and the harness `Message` type.
     2. Preserve tool-call IDs across requests.
     3. Forward `AbortSignal` to HTTP clients or SDK calls.
     4. Normalize provider HTTP / API errors into thrown exceptions that the harness catches as `model_error`.
   - **Seam Rule**: Adding or modifying provider adapters requires zero modifications to the core agent loop, tool registry, workspace sandbox, budget manager, or context windowing components.
5. **Completion Gate**: 150 seeded batch property tests and 60 tool exception recovery runs pass deterministically; observer failure tests verify harmless isolation; provider adapter coaching rubric is verified.

---

## Bundled Tooling & CLI Seams

This skill includes an executable domain engine and headless Click CLI seam under `scripts/`:

```bash
# 1. Audit a codebase against the 9 binary diagnostic seam gates
python scripts/ts_harness_constructor.py audit --target-dir <path> [--json]

# 2. Run 150-run seeded PRNG batch property simulation (Rule 12/43)
python scripts/ts_harness_constructor.py simulate --seed 0x12345678 --runs 150 [--json]

# 3. Scaffold complete zero-dependency TypeScript harness boilerplate
python scripts/ts_harness_constructor.py scaffold --output-dir <path> [--json]
```

Key slotted domain models in [`scripts/ts_harness_engine.py`](scripts/ts_harness_engine.py):
- `HarnessBudgetConfig` — Mathematical budgets and operational thresholds.
- `ToolContractDefinition` — Schema validation and error bifurcation.
- `WorkspaceSandboxPolicy` — Ancestor `lstat()` walk and lexical confinement.
- `AtomicBudgetEvaluator` — Pre-transcript batch budget verification.
- `ContextWindowManager` — Atomic turn group sliding allocation.
- `PRNGBatchSimulator` — Deterministic property testing with zero orphaned calls.

---

## Mandatory Checkpoint

Before finalizing harness implementation or deploying to production, execute this mandatory checkpoint gate:

> [!CAUTION]
> **Harness Confinement & Budget Verification Checkpoint**:
> - [ ] Assert that `Workspace.open()` performs an ancestor `lstat()` walk and rejects symlinked parent paths.
> - [ ] Assert that command presets execute with `shell: false` and strict timeout kill handlers.
> - [ ] Assert that tool batches exceeding remaining `maxToolCalls` are rejected atomically without writing to the transcript.
> - [ ] Assert that `onEvent` telemetry dispatches are isolated so observer crashes cannot alter run status.

---

## Diagnostic Coaching Rubrics — Binary Pass/Fail Gates

| Seam | Diagnostic Question | **PASS** | **FAIL** |
|---|---|---|---|
| **Tool Validation** | Does argument validation happen before `tool.execute()`? | Schema validation runs; invalid input returns `role:'tool'` error; `execute()` never called. | Arguments passed directly to implementation; type errors crash at runtime. |
| **Error Bifurcation** | Are tool runtime errors segregated from model provider failures? | Tool exceptions ➔ recoverable feedback message. Model provider crash ➔ `status:'model_error'` termination. | Conflating provider downtime with recoverable tool errors. |
| **Filesystem Sandboxing** | Are symlinks verified across all intermediate directory components? | Iterative `lstat` walk on every ancestor; lexical escape check; `O_NOFOLLOW` on file open. | Only final path target checked; symlinked parent directory allows escape. |
| **Command Hardening** | Can the model supply an executable path, extra args, or shell syntax? | Named preset selection only; hardcoded executable; `shell: false`; timeout; buffer cap. | Raw shell string interpolation or `child_process.exec()` with model-supplied input. |
| **Atomic Batch Budget** | Is the tool budget checked before mutating conversation history? | Budget verified before assistant message appended; rejected batches: 0 calls executed, 0 transcript traces. | Assistant message with tool calls appended, then budget exceeded mid-batch ➔ orphaned calls in transcript. |
| **Context Group Integrity** | Does context sliding preserve indivisible tool-call/result pairs? | All tool results for an assistant turn kept with or removed with their parent turn. | Sliding window drops tool results while retaining the assistant tool-call message. |
| **Observer Isolation** | Can a telemetry listener exception corrupt the agent outcome? | All `onEvent` invocations wrapped in isolated `try...catch`; listener errors suppressed. | Observer throws ➔ successful tool run recorded as failure. |
| **Deterministic Evals** | Are boundary conditions tested without live API calls or token cost? | `scriptedModel` + 150 seeded PRNG scenarios + 60 exception recovery loops. | Only happy-path tested or live LLM endpoints used in boundary tests. |
| **Provider Seam Isolation** | Does adding a real LLM provider require changing any harness component? | `Model` interface is the sole seam; adapter translates format, preserves call IDs, forwards signal. | Harness loop modified per provider; registry or context changes needed per model. |

---

## Anti-Patterns

- **Tool Trust Vulnerability** — Passing raw model arguments directly to tool implementations without schema validation. Harness must validate against declared schema; invalid arguments return an error message without calling execute().
- **Unbounded Shell Injection** — Permitting the model to synthesize raw shell strings or select arbitrary executables. Harness must restrict execution to developer-defined presets with shell: false and fixed argument arrays.
- **Workspace Sandbox Bypass** — Checking only the final file path for traversal or symlink violations, while ignoring parent directory components. Harness must walk every ancestor with lstat and use O_NOFOLLOW at the file open boundary.
- **Premature Transcript Mutation** — Appending an assistant tool-call message before verifying that the entire batch fits within the remaining tool budget. Harness must check budget atomically before transcript mutation; rejected batches must leave zero traces.
- **Coupled Telemetry Failure** — Allowing exceptions in observer or logging callbacks to fail an otherwise successful agent run. All onEvent dispatches must be wrapped in isolated try...catch whose failures are independently suppressed.
- **Silent Cost Opacity** — Treating absent or null token usage fields from the model provider as zero tokens consumed. Harness must accumulate modelCallsWithUsage separately and surface unknown cost explicitly rather than presenting a misleading 0 total.
