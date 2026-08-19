# Quick Start Guide: `plugin.symbolic_solver` (v1.0.0)

> Neuro-symbolic constraint solver, logic deduction, and safe arithmetic evaluation

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`solve_constraints`**: Find satisfiable assignments for variables given mathematical and logical constraints
- **`verify_logic_query`**: Perform logical deduction over a set of facts and inference rules
- **`evaluate_math_expression`**: Safely parse and calculate complex mathematical expressions without unsafe eval

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('plugin.symbolic_solver.solve_constraints', {'variables': '<variables>', 'constraints': '<constraints>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider plugin.symbolic_solver
harness plugin enable plugin.symbolic_solver
```

## ⚡ Available Entrypoints & Skills
- **`solve_constraints(variables: array, constraints: array)`**
  Find satisfiable assignments for variables given mathematical and logical constraints
- **`verify_logic_query(facts: array, rules: array, query: string)`**
  Perform logical deduction over a set of facts and inference rules
- **`evaluate_math_expression(expression: string)`**
  Safely parse and calculate complex mathematical expressions without unsafe eval