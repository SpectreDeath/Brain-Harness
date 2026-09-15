# plugin.symbolic_solver (v1.0.0)

Neuro-symbolic constraint solver, safe arithmetic evaluation, and Horn-clause rule engine

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/integration_and_io/symbolic_solver` |
| Category | `integration_and_io` |
| Isolation Mode | `in_process` |
| Services Provided | `service.symbolic_solver` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `evaluate_math_expression` | `(expression)` | Safely evaluate mathematical and logic expressions without eval() vulnerability |
| `solve_constraints` | `(variables, constraints)` | Find satisfiable assignments for variables across a set of mathematical constraints |
| `verify_logic_query` | `(facts, rules, query)` | Verify whether a query statement holds given known facts and deduction rules |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Neuro-symbolic constraint solver and logic evaluation tools.

#### Classes

- `class SymbolicSolverPlugin` — Harness Plugin providing neuro-symbolic math evaluation, constraint solving, and logic queries.
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`
  - `def evaluate_math_expression(expression) -> MathEvalResult`
  - `def solve_constraints(variables, constraints) -> ConstraintSolveResult`
  - `def verify_logic_query(facts, rules, query) -> LogicQueryResult`


#### Functions

- `def evaluate_math_expression(expression) -> dict[str, Any]` — Safely calculate a mathematical expression using AST parsing.
- `def solve_constraints(variables, constraints) -> dict[str, Any]` — Find satisfiable assignments for integer/float variables across constraints.
- `def verify_logic_query(facts, rules, query) -> dict[str, Any]` — Evaluate logic query against facts database.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.integration_and_io.symbolic_solver.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
