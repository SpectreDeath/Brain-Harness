# Knowledge Vault Item: Pi-Style Minimalist Coding Agent Harness Architecture

**ID**: `ki_20260922_tau_pi_agent_architecture`  
**Source**: Tau Repository (`D:\GitHub\cloned\tau`, v0.4.4, commit `681275b`) & Pi architecture by Mario Zupan  
**Status**: VERIFIED  

---

## 1. Epistemic Architecture & The Three-Tier Separation

Pi-style agent harnesses resolve the problem of coding agent bloat by enforcing an uncompromising three-tier architectural division:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Provider Streaming Layer (tau_ai)                        │
│ - Normalized stream events, token counters, retry loops     │
│ - Zero harness state, zero tool execution logic             │
├─────────────────────────────────────────────────────────────┤
│ 2. Portable Agent Brain Layer (tau_agent)                   │
│ - Reusable harness, agent loop, cancellation tokens         │
│ - Branchable session trees, append-only locked storage      │
│ - Zero UI, CLI, Rich, or Textual dependencies               │
├─────────────────────────────────────────────────────────────┤
│ 3. Coding Application Environment (tau_coding)              │
│ - Typer CLI, Textual interactive TUI, dynamic extensions   │
│ - Project trust boundaries, bash/edit tools, JSON-RPC seam │
└─────────────────────────────────────────────────────────────┘
```

### Key Mental Model: Event Inversion
Instead of the agent loop directly driving UI elements, the core loop is an asynchronous generator emitting fine-grained domain events:
- `AgentStartEvent`, `TurnStartEvent`
- `MessageStartEvent`, `MessageUpdateEvent`, `MessageEndEvent`
- `ToolExecutionStartEvent`, `ToolExecutionEndEvent`
- `TurnEndEvent`, `AgentEndEvent`

The frontend (whether a full-terminal Textual TUI, a simple stdout pipe, or an IDE extension over JSON-RPC) is merely a passive subscriber.

---

## 2. Branchable Session Trees & Append-Only Journals

Traditional agent harnesses store sessions as flat arrays of messages (`list[Message]`). When a user rewinds or branches a conversation, traditional systems either truncate the file or fork copies of the entire JSON file.

Tau and Pi solve this via **Immutable DAG Entries**:
1. Every entry has an `id` and an optional `parent_id`.
2. A conversation branch is identified solely by the `id` of its leaf entry.
3. Resolving the active prompt context is an $O(N)$ traversal from leaf to root:
   ```python
   curr = leaf_id
   while curr is not None:
       node = nodes[curr]
       path.append(node)
       curr = node.parent_id
   return reversed(path)
   ```
4. **Append-Only Journaling**: All entries are written to a single `.jsonl` file with advisory file locking. Branching, undoing, and replaying require zero file truncations or mutations.

---

## 3. In-Flight Provider-Safe Tool History Normalization

When multi-agent loops or humans interrupt tool executions, conversation histories often contain mismatched tool calls:
- Assistant message requests `call_123`, but user cancels before tool execution occurs.
- Subsequent turn submits raw history to Anthropic Claude or OpenAI, which immediately returns `HTTP 400: invalid_request_error: Expected tool result for call_123`.

### The Pi-Style Repair Heuristic
Prior to submitting messages to the model provider:
1. **Orphan Drop**: Drop any `tool` message whose `tool_call_id` does not match an assistant tool call in the preceding block.
2. **Deterministic Placeholder Synthesis**: For any assistant `tool_call` that lacks a following `tool` result message, synthesize a neutral placeholder result:
   ```json
   {
     "role": "tool",
     "tool_call_id": "<unresponded_id>",
     "content": "[Notice: Tool execution was interrupted or missing in transcript]"
   }
   ```
This guarantees 100% provider parity without requiring user reprompts.

---

## 4. Hierarchical Project Trust & Sandboxing

A coding agent given raw terminal tools (`bash`, `write`, `edit`) poses immediate security risks if launched in untrusted repositories.

Tau implements **Hierarchical Project Trust**:
1. **Git Root Scoping**: Finds the nearest enclosing `.git` boundary. Workspaces outside version control are treated as `RESTRICTED`.
2. **Protected Asset Isolation**: Scans for sensitive files (`.env`, `credentials.json`, `id_rsa`, `.git/config`). If private SSH keys are present, execution is locked to `BLOCKED`.
3. **Parent Inheritance**: If a parent directory has been explicitly approved by the developer, child subprojects inherit trust automatically.

---

## 5. Decision Heuristics & Defensive Invariants

- **Invariant 1**: Never import UI libraries (`textual`, `rich`, `click`, `typer`) inside the cognitive agent loop package.
- **Invariant 2**: Store session entries in append-only streams; never rewrite or truncate historical session journal files.
- **Invariant 3**: Always run in-flight tool history repair before dispatching payloads to external model provider APIs.
- **Invariant 4**: Enforce project trust gates before allowing automated bash tool execution or loading workspace plugins.
