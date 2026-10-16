# Tau Harness Bridge Plugin (`plugin.tau_harness_bridge`)

## Overview

The `tau_harness_bridge` plugin brings Pi-style minimalist coding agent harness mechanics into Brain Harness. Synthesized from **Tau** (`huggingface/tau` v0.4.4) and Mario Zupan's Pi architecture, it provides:

1. **Branchable Session Tree DAGs**: Conversation entries are modeled as directed acyclic graph nodes (`id`, `parent_id`), allowing non-destructive branching, rewinding, and linear ancestry resolution (`resolve_session_path`).
2. **Provider-Safe Tool History Repair**: Intercepts and normalizes conversation transcripts before model submission (`repair_tool_history`), pruning orphan tool outputs and synthesizing placeholders for unresponded calls to eliminate HTTP 400 errors across Anthropic, Mistral, and OpenAI.
3. **Workspace Project Trust & Security Gates**: Evaluates project security postures, detecting untrusted roots, parent Git boundaries, and sensitive assets (`.env`, private keys) prior to agent tool execution.
4. **Pi-Compatible JSON-RPC Envelopes**: Enables headless background agent runners and IDE extensions to communicate over streaming JSONL RPC protocol.

## Service Key

```python
from harness.services.tau_bridge import TAU_HARNESS_BRIDGE_SERVICE_KEY, TauBridgeService

# Resolve from IoC context
tau_bridge = context.require(TAU_HARNESS_BRIDGE_SERVICE_KEY)
```

## Exported Tools

- `tau_session_fork`: Resolves linear ancestry from root to a chosen branch node.
- `tau_tool_history_repair`: In-flight repair of malformed tool call histories.
- `tau_project_trust_eval`: Evaluates directory permissions and protected files.
- `tau_rpc_session_dispatch`: Formats JSON-RPC 2.0 protocol envelopes.


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `tau_session_fork` | `(entries, target_id)` | Traverse branchable session tree DAG entries and resolve linear ancestry path from root to target entry |
| `tau_tool_history_repair` | `(messages)` | Normalize message history in-flight to repair orphan tool responses or unresponded assistant tool calls |
| `tau_project_trust_eval` | `(project_path, trusted_roots)` | Evaluate workspace security boundaries, git root inheritance, and sensitive file exposures |
| `tau_rpc_session_dispatch` | `(request_id, result, error)` | Format or dispatch a Pi-compatible JSONL RPC protocol envelope for headless runner execution |
