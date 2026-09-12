# domain.human_in_the_loop (v1.0.0)

Human-in-the-loop permission escalation gate, decision checkpoints, and approval audit ledger

---

## Overview & Metadata

- **Plugin Directory**: `plugins/agent_orchestration/human_in_the_loop`
- **Isolation Mode**: `in_process`
- **Services Provided**: None
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `request_human_approval` | `(action_name, risk_level, details)` | Create a pending approval request for a sensitive tool call or state transition (e.g. database drop, code push) |
| `record_human_decision` | `(request_id, approved, reason)` | Record human operator decision (approved / rejected) for an approval request |
| `list_pending_approvals` | `()` | List all active approvals awaiting human decision |

---

## Key Modules & AST Symbols

### Module [`main.py`](main.py)

Human-in-the-loop permission escalation and approval ledger plugin.

#### Functions

- `def request_human_approval(action_name, risk_level, details) -> dict[str, Any]`
  - Register a pending human approval request.
- `def record_human_decision(request_id, approved, reason) -> dict[str, Any]`
  - Record operator decision on an approval request.
- `def list_pending_approvals() -> dict[str, Any]`
  - List all pending approval requests.



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
