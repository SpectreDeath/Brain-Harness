# Knowledge Item: Zero-Dependency AI Agent Harness Construction in TypeScript

## Epistemic Distillation

### 1. Ground-Truth Mental Models

#### The Loop as a State Machine & ReAct Cycle
A resilient AI agent harness does not rely on opaque third-party frameworks. At its core, the harness is a deterministic state machine managing a ReAct (Reasoning + Action) execution loop:
1. Append the initial user prompt to the immutable message list.
2. In each turn, submit the current conversation history to the decoupled model provider.
3. If the model returns text without tool calls, complete the run with `status: 'completed'`.
4. If the model requests tool calls, validate arguments against declared schemas, check remaining invocation budgets atomically, and execute tools.
5. Append tool results to the conversation history and loop back to step 2 until `maxSteps`, `maxToolCalls`, or external cancellation triggers termination.

#### Error Bifurcation Model: Recoverable Feedback vs Terminal Infrastructure Failure
Agent reliability depends on distinguishing model cognitive mistakes from external infrastructure failures:
- **Tool Failures (Recoverable)**: Schema validation rejections, missing tool registrations, or exceptions thrown during tool execution represent actionable feedback. The harness catches the exception, formats a `role: 'tool'` message with `isError: true`, and returns it to the model. The model reflects on the error and can correct its parameters on the subsequent turn.
- **Model Provider Failures (Terminal)**: Network timeouts, 401 Unauthorized, 429 Rate Limits, or model process crashes are infrastructure failures. The model cannot reason about its own inability to generate. The harness terminates immediately with `status: 'model_error'`.

#### Confinement in Depth: Multi-Layer Filesystem Sandboxing
Checking only the final target path of a file operation is an illusion of security. An attacker or hallucinating model can exploit symbolic links in parent directories to escape the workspace root. Robust workspace sandboxing requires four synchronized layers:
1. **Canonical Root Resolution**: Resolve the workspace root using `fs.realpath` at boot to establish the true canonical path.
2. **Lexical Confinement**: Verify `path.resolve(root, input)` begins with `root` and `path.relative(root, resolved)` does not start with `..`.
3. **Ancestor `lstat` Walk**: Walk every parent directory from the resolved path up to the root, calling `fs.lstat()`. If any intermediate directory has `stats.isSymbolicLink() === true`, reject the operation immediately.
4. **File Open Flag (`O_NOFOLLOW`)**: Use `fs.constants.O_NOFOLLOW` when opening file descriptors to eliminate race conditions between path validation and file opening.

#### Hardened Command Presets: Eliminating Shell Injection
Allowing an agent to pass arbitrary strings to `child_process.exec()` or assemble CLI arguments invites catastrophic shell injection.
- **Preset Isolation**: Developers define fixed command structures (`name`, `executable`, `args[]`, `timeoutMs`).
- **Constrained Model Intent**: The model is permitted to choose presets strictly by `name`; it cannot specify executables, add extra flags, or invoke shell operators (`|`, `&&`, `;`).
- **Process Guardrails**: Child processes are spawned with `shell: false`, terminated via `SIGTERM`/`SIGKILL` on timeout, and bounded by strict 64 KB buffers on both `stdout` and `stderr` to prevent memory exhaustion attacks.

#### Atomic Batch Budget Invariant: Zero Orphaned Tool Calls
When a model emits a batch of multiple tool calls in a single turn, checking the tool budget one call at a time is hazardous. If the budget is exhausted on the second of four calls, the conversation transcript contains an assistant message requesting four tools, but only two have answers. On subsequent turns, the model encounters a corrupted conversational history with unfulfilled promises.
- **The Invariant**: Prior to mutating the conversation transcript or executing any tool in the batch, assert:
  $$\text{batch.length} \le \text{maxToolCalls} - \text{cumulativeToolCalls}$$
- If the batch exceeds the remaining budget, reject the entire batch, do not append the assistant message, and terminate immediately with `status: 'tool_limit'`.

#### Indivisible Turn Groups in Context Sliding
Sliding context windows that drop individual messages line-by-line cause transcript corruption by separating assistant tool calls from their corresponding tool outputs.
- **Atomic Turn Grouping**: Group messages into indivisible units:
  - Initial User Prompt
  - Compound Turn: Assistant Tool Calls + All Corresponding Tool Results
  - Final Assistant Answer
- Windowing algorithms must accumulate whole groups backward from the most recent turn. If a group cannot fit within the remaining character budget, the entire group is dropped together, preserving conversation coherency.

#### Observer Isolation Invariant
Observability is a passive listener, never a blocker. If an `onEvent` callback (metrics logger, OpenTelemetry exporter, or terminal UI) throws an unhandled exception, that exception must be trapped, routed to an optional error handler, and suppressed. Telemetry errors must never fail an otherwise successful agent execution.

---

### 2. Provider Adapter Architecture

Real LLMs (Anthropic Claude, OpenAI, Google Gemini, Ollama) connect strictly through the single provider interface:

```typescript
export interface Model {
  generate(params: {
    messages: Message[];
    tools?: ToolDefinition[];
    signal?: AbortSignal;
  }): Promise<ModelResponse>;
}
```

Adapters encapsulate all provider-specific concerns:
1. Translating internal `Message` structures into provider wire formats.
2. Preserving and mapping tool-call IDs across requests.
3. Forwarding `AbortSignal` to HTTP clients (e.g. `fetch` or SDK clients).
4. Normalizing HTTP status codes (401, 429, 500) into thrown errors that the harness handles as `model_error`.

Because this interface is the sole seam, swapping model providers requires zero changes to the agent loop, tool registry, workspace sandbox, budget manager, or context window engine.

---

### 3. Seeded Deterministic Testing Heuristics

Production agent harnesses cannot rely on flaky, expensive live API calls for regression testing:
- **`scriptedModel`**: Advances through an array of pre-configured responses, throwing `'Scripted model exhausted'` on unexpected calls.
- **PRNG Batch Scenarios**: Use a pseudo-random number generator initialized with a fixed seed (`0x12345678`) to execute 150 randomized batch tests, varying `limit ∈ [0, 8]` and `batch ∈ [0, 12]`. This mathematically proves that admitted batches execute 100% of calls and rejected batches execute 0% with zero transcript side effects.
- **Exception Recovery Stress Tests**: Run 60 consecutive recovery loops asserting that tool execution exceptions are properly reflected into `role: 'tool'` error observations while model provider exceptions terminate the loop cleanly.
