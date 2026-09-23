---
name: pi-coding-harness
description: Architect, construct, sandbox, and evaluate portable terminal coding agents using decoupled 3-tier layering, branchable session tree DAGs, append-only JSONL storage, provider-safe tool history repair, and project-trust security gates. Do not use for generic single-turn chat, open-ended writing, or ungrounded script generation.
---

# Pi-Style Minimalist Coding Agent Harness Architecture

`pi-coding-harness` is the authoritative engineering framework for designing, implementing, sandboxing, and evaluating minimalist, portable terminal coding agents. Grounded in **Tau** (`huggingface/tau` v0.4.4) and Mario Zupan's Pi architecture, it enforces strict separation between model streaming, portable agent cognition, and interactive frontends.

Every Pi-style coding harness follows a strict 5-stage progression:

```
[1. Architecture Decoupling] ──► [2. Branchable Session DAG] ──► [3. Append-Only Journal]
                                                                        │
                                                                        ▼
[5. Trust & RPC Governance] ◄── [4. In-Flight Tool Repair] ◄────────────┘
```

See [CARD.md](CARD.md) for the companion summary card, 5-stage progression matrix, and operational invariants.
Consult [tau_harness_bridge](../../plugins/agent_orchestration/tau_harness_bridge/README.md) for the in-memory micro-kernel IoC service integration.

---

## 1. Architecture Decoupling (The Three-Tier Separation)

Enforce rigid boundaries between streaming inference, portable cognition, and user interface layers:

1. **Partition into Three Isolated Layers**:
   - **Streaming Layer (`tau_ai`)**: Manages model provider streaming, SSE stream parsing, token counting, retry loops, and neutral chunk emission. Contains zero agent or tool state.
   - **Agent Kernel Layer (`tau_agent`)**: Reusable brain containing `AgentHarness`, `run_agent_loop`, message queues, cancellation tokens, session trees, and tool execution protocols. Free from CLI, Rich, Textual, or filesystem layout assumptions.
   - **Coding Environment Layer (`tau_coding`)**: Interactive CLI (Typer), interactive TUI (Textual), file reading/writing/editing tools, dynamic extensions, project trust policies, and JSON-RPC daemon.
2. **Invert the Control Flow**:
   - The agent harness emits fine-grained events (`TurnStartEvent`, `MessageUpdateEvent`, `ToolExecutionStartEvent`, `TurnEndEvent`).
   - Frontends (Textual TUI, CLI, Web dashboards) subscribe to the event stream as read-only consumers without polluting the execution loop.

> **Completion criterion**: Core loop runs headlessly without importing or referencing any TUI, CLI, or frontend renderer classes.

---

## 2. Branchable Session DAG Setup

Model conversation history as an immutable directed acyclic graph rather than a flat linear list:

1. **Anchor Entries with Parent Pointers**:
   - Every session entry declares an immutable `id` and `parent_id` (`parent_id: null` for conversation root).
   - User inputs, assistant thoughts, tool calls, tool results, and system notices are recorded as distinct DAG entries.
2. **Resolve Linear Ancestry On-the-Fly**:
   - To construct the active LLM context window, traverse upwards from `target_entry_id` along `parent_id` links to the root.
   - Reverse the sequence to form the exact chronological trajectory for that branch.
3. **Non-Destructive Conversation Forking**:
   - Branching is achieved simply by creating a new entry whose `parent_id` references an older historical entry.
   - Historical branches remain intact without truncating or mutating existing entries.

> **Completion criterion**: `resolve_session_path` resolves correct $O(N)$ linear ancestry for any fork node and rejects cyclic graphs.

---

## 3. Append-Only Journal Locking

Guarantee durability and crash safety using single-file locked append-only storage:

1. **Immutable JSONL Journaling**:
   - Every session is serialized as an append-only JSONL file where each line is an entry payload.
   - Never rewrite, truncate, or re-order lines in the session journal.
2. **Advisory File Locking**:
   - Acquire non-blocking advisory file locks (`fcntl.flock` on POSIX, `msvcrt.locking` on Windows) before writing new entries.
   - Release the lock immediately after flush to prevent contention with background readers or multi-process observers.

> **Completion criterion**: Session state survives abrupt process termination without file corruption or partial-line writes.

---

## 4. In-Flight Provider-Safe Tool History Repair

Prevent model provider API failures caused by interrupted or malformed tool call transcripts:

1. **Enforce Interleaved Tool Call Parity**:
   - Modern LLM APIs (Anthropic Claude, OpenAI, Mistral) reject requests with HTTP 400 if an assistant `tool_calls` block lacks matching `tool` result messages, or if an orphan `tool` message appears without an antecedent.
2. **Apply Multi-Pass In-Flight Repair**:
   - **Orphan Pruning**: Drop tool response messages that have no matching antecedent `tool_call_id`.
   - **Placeholder Synthesis**: If an assistant message issued a `tool_call` that was cancelled, timed out, or crashed before emitting a result, synthesize a deterministic notice payload: `"[Notice: Tool execution was interrupted or missing in transcript]"`.
   - **Sequence Grouping**: Align all tool result messages immediately following the assistant tool invocation block.

> **Completion criterion**: Repaired message histories guarantee 100% parity between tool call IDs and tool result IDs prior to model dispatch.

---

## 5. Trust & RPC Governance

Protect host workspaces and expose standardized headless remote control seams:

1. **Project Trust Perimeter**:
   - Inspect target repository boundaries before running shell commands or loading workspace extensions.
   - Detect and flag sensitive credentials (`.env`, `credentials.json`, `id_rsa`, `.git/config`).
   - Assign permission tiers: `TRUSTED` (full execution), `RESTRICTED` (read-only), `BLOCKED` (sensitive keys exposed).
2. **Headless JSON-RPC Seam**:
   - Implement JSON-RPC 2.0 streaming envelopes over standard I/O for embedding the coding agent into IDEs, MCP bridges, or background cron schedulers.

> **Completion criterion**: Workspace trust boundaries evaluated and JSON-RPC daemon dispatches valid 2.0 protocol envelopes.

---

## Diagnostic Coaching Scorecard

| Check Item | Pass Standard | Failure Indicator |
|---|---|---|
| **Loop Independence** | Zero UI imports in agent loop package | Importing Textual/Rich inside `tau_agent` |
| **DAG Integrity** | Entries resolve to root with cycle detection | Cyclic parent pointers causing infinite loop |
| **Storage Safety** | File-locked append-only JSONL | In-place file truncation or JSON array rewriting |
| **Tool History Parity** | 100% match between call IDs and result IDs | Unpaired tool calls triggering provider 400 |
| **Security Perimeter** | Sensitive files detected before execution | Reading or leaking `.env` / SSH private keys |

---

## Anti-Patterns

- **Loop UI Coupling** — Importing terminal renderers, CLI widgets, or interactive prompts directly into core agent loop modules.
- **Destructive History Truncation** — Overwriting or deleting session files when the user rewinds or changes branches instead of appending DAG nodes.
- **Unrepaired Tool Desync** — Passing unresponded tool calls or orphan results directly to LLM provider APIs, causing 400 Bad Request crashes.
- **Unverified Workspace Execution** — Executing commands or loading external extensions in untrusted workspaces without evaluating trust boundaries.
- **Monolithic State Sprawl** — Storing UI configuration, model tokens, and conversation messages in a single mutable dictionary instead of slotted frozen dataclasses.
