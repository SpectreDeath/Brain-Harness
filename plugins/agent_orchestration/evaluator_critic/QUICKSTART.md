# Quick Start Guide: `plugin.evaluator_critic` (v1.0.0)

> Adversarial code review, AST static analysis, destructive command safety filter, and plan feasibility critique

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`critic_evaluate_code`**: Statically analyze code syntax, complexity, function docstrings, and potential anti-patterns
- **`critic_review_plan`**: Evaluate an execution plan for logical consistency, risk factors, and missing dependencies
- **`critic_check_safety`**: Scan a CLI shell command for dangerous or irreversible operations

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('plugin.evaluator_critic.critic_evaluate_code', {'code': '<code>', 'language': '<language>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider plugin.evaluator_critic
harness plugin enable plugin.evaluator_critic
```

## ⚡ Available Entrypoints & Skills
- **`critic_evaluate_code(code: string, language: string)`**
  Statically analyze code syntax, complexity, function docstrings, and potential anti-patterns
- **`critic_review_plan(goal: string, steps: array)`**
  Evaluate an execution plan for logical consistency, risk factors, and missing dependencies
- **`critic_check_safety(command: string)`**
  Scan a CLI shell command for dangerous or irreversible operations