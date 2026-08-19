# Quick Start Guide: `domain.trajectory_auditor` (v1.0.0)

> Agent trajectory step auditor, repetitive loop / stuck detector, and recovery prompt synthesizer

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`audit_trajectory_steps`**: Analyze an agent's execution history for repeated tool failures, excessive step counts, and inefficiency
- **`detect_repetitive_loop`**: Detect cyclic repetition in agent action sequences (e.g. A -> B -> A -> B)
- **`synthesize_recovery_prompt`**: Generate an intervention prompt to break an agent out of a stuck loop or error cycle

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.trajectory_auditor.audit_trajectory_steps', {'steps': '<steps>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.trajectory_auditor
harness plugin enable domain.trajectory_auditor
```

## ⚡ Available Entrypoints & Skills
- **`audit_trajectory_steps(steps: array)`**
  Analyze an agent's execution history for repeated tool failures, excessive step counts, and inefficiency
- **`detect_repetitive_loop(actions: array, window_size: integer)`**
  Detect cyclic repetition in agent action sequences (e.g. A -> B -> A -> B)
- **`synthesize_recovery_prompt(stuck_reason: string, last_failed_action: string)`**
  Generate an intervention prompt to break an agent out of a stuck loop or error cycle