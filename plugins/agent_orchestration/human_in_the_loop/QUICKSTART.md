# Quick Start Guide: `domain.human_in_the_loop` (v1.0.0)

> Human-in-the-loop permission escalation gate, decision checkpoints, and approval audit ledger

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`request_human_approval`**: Create a pending approval request for a sensitive tool call or state transition (e.g. database drop, code push)
- **`record_human_decision`**: Record human operator decision (approved / rejected) for an approval request
- **`list_pending_approvals`**: List all active approvals awaiting human decision

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.human_in_the_loop.request_human_approval', {'action_name': '<action_name>', 'risk_level': '<risk_level>', 'details': '<details>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.human_in_the_loop
harness plugin enable domain.human_in_the_loop
```

## ⚡ Available Entrypoints & Skills
- **`request_human_approval(action_name: string, risk_level: string, details: object)`**
  Create a pending approval request for a sensitive tool call or state transition (e.g. database drop, code push)
- **`record_human_decision(request_id: string, approved: boolean, reason: string)`**
  Record human operator decision (approved / rejected) for an approval request
- **`list_pending_approvals()`**
  List all active approvals awaiting human decision