# Skill Summary Card: `ts-agent-harness-constructor`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:       ts-agent-harness-constructor              │
│ Category:    agent_orchestration / runtime_harness     │
│ Invocation:  /ts-agent-harness-constructor             │
│ Trigger:     "build an agent harness in typescript",   │
│              "zero-dependency typescript agent loop",  │
│              "validate tool arguments before exec",    │
│              "sandbox workspace file operations",      │
│              "lock down command execution to presets", │
│              "atomic tool batch budget check",         │
│              "seeded failure testing agent",           │
│              "provider-agnostic model interface"       │
│ Version:     1.0.0                                     │
│ Provides:    "typescript_agent_harness_construction",  │
│              "tool_contract_registry",                 │
│              "workspace_confinement_pattern",          │
│              "agent_failure_testing"                   │
├────────────────────────────────────────────────────────┤
│ Target:      Construct, validate, and harden           │
│              zero-dependency AI agent runtime          │
│              harnesses in TypeScript and Node.js.      │
└────────────────────────────────────────────────────────┘
```

---

## The 6-Stage Harness Construction Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Loop & Model Abstraction** | Decouple provider behind `Model` interface; build `scriptedModel` | `runAgent()` + `scriptedModel` | Basic loop tests pass covering tools, limit, and abort |
| **2. Contract Registry & Validation** | Validate arguments against schema; bifurcate tool vs model errors | `ToolRegistry` + Schema Validator | Invalid arguments never reach `execute()`; model crashes yield `model_error` |
| **3. Workspace Containment & Presets** | Confine paths via ancestor `lstat` walk; restrict commands to presets | `Workspace.open()` + Command Presets | Symlinks in intermediate paths rejected; commands strictly `shell: false` |
| **4. Execution Limits & Cancellation** | Enforce `maxSteps` and `maxToolCalls`; atomic batch verification | Budget Manager + `AbortSignal` | 150 seeded PRNG batch tests pass; rejected batches leave 0 transcript traces |
| **5. Atomic Context Windowing** | Sliding window preserving indivisible tool-call/result pairs | `selectContext()` Windowing Engine | Batch indivisibility preserved; orphan tool results detected and rejected |
| **6. Telemetry, Evals & Adapters** | Isolated `onEvent` telemetry; token tracking; model adapter pattern | Lifecycle Telemetry + Adapter Pattern | Observer exceptions safely isolated; 60 tool recovery tests pass |

---

## Architecture Cheat Sheet

### 1. Error Bifurcation Model
- **Tool Failure (Recoverable)**: Unknown tool, schema validation failure, or exception thrown inside `tool.execute()` ➔ Synthesize `role: 'tool'` message with `isError: true`. Model observes error and retries on next turn.
- **Model Failure (Terminal)**: `model.generate()` throws (network crash, authentication failure, quota exhaustion) ➔ Terminate immediately with `status: 'model_error'`.

### 2. Workspace Confinement Boundary
- **Canonical Root**: `await realpath(root)` at initialization.
- **Lexical Check**: `resolve(root, input)` + `relative(root, resolved)` ensuring path stays within boundary.
- **Ancestor Symlink Walk**: Component-by-component `lstat()` walk on all parent directories rejecting symlinks.
- **File Open Safety**: Open file handles with `O_NOFOLLOW` flag.

### 3. Atomic Batch Budget Invariant
- Check `calls.length <= (maxToolCalls - cumulativeCalls)` **before** appending assistant message to transcript.
- If over budget, terminate with `status: 'tool_limit'` immediately.
- Never partially execute tool batches or leave unfulfilled assistant tool calls in transcript.

### 4. Provider Adapter Isolation Seam
- Real LLMs connect solely through `Model` interface (`generate({ messages, tools, signal })`).
- Adapters translate provider wire format, maintain tool call IDs, and forward `AbortSignal`.
- Adding new model providers requires **zero changes** to loop, registry, workspace jail, budget, or context engine.

### 5. Headless Construction Tooling
- `python scripts/ts_harness_constructor.py simulate --runs 150`: Deterministic PRNG batch verification.
- `python scripts/ts_harness_constructor.py scaffold -o <path>`: Scaffolds 7 zero-dependency TypeScript modules.
- `python scripts/ts_harness_constructor.py audit -t <path>`: Evaluates 9 diagnostic seam scorecards.

---

## Mandatory Invariants Checklist

- [ ] **Pre-Dispatch Validation**: Tool arguments are validated against JSON Schema prior to calling `tool.execute()`.
- [ ] **Ancestor Symlink Verification**: `Workspace.open()` walks all parent directories via `lstat()` to reject symlink traversal escapes.
- [ ] **Hardened Command Presets**: Commands execute solely via predefined developer presets with `shell: false` and strict timeout killing.
- [ ] **Atomic Tool Batch Budgeting**: Batches exceeding remaining tool budget are rejected prior to transcript mutation.
- [ ] **Context Indivisibility**: Context sliding treats assistant turns and their associated tool results as atomic, indivisible groups.
- [ ] **Observer Crash Isolation**: All `onEvent` listener dispatches are wrapped in isolated `try...catch` blocks to prevent telemetry exceptions from failing agent runs.
- [ ] **Seeded Deterministic Testing**: Harness boundary behaviors are verified using `scriptedModel` and deterministic PRNG seeds without live network dependencies.
