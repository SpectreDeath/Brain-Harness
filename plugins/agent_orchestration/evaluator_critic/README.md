# plugin.evaluator_critic (v1.0.0)

Adversarial code review, AST static analysis, destructive command safety filter, and plan feasibility critique

---

## Overview & Metadata

- **Plugin Directory**: `plugins/agent_orchestration/evaluator_critic`
- **Isolation Mode**: `in_process`
- **Services Provided**: `service.critic_evaluation`
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `critic_evaluate_code` | `(code, language)` | Statically analyze code syntax, complexity, function docstrings, and potential anti-patterns |
| `critic_review_plan` | `(goal, steps)` | Evaluate an execution plan for logical consistency, risk factors, and missing dependencies |
| `critic_check_safety` | `(command)` | Scan a CLI shell command for dangerous or irreversible operations |

---

## Key Modules & AST Symbols

### Module [`main.py`](main.py)

Evaluator, Critic, and Safety Gatekeeper Plugin (Thin Adapter).

Delegates to the authoritative CriticEvaluationService seam while maintaining
100% backward-compatible function signatures and entrypoint contracts.

#### Classes

- `class EvaluatorCriticPlugin`
  Adapter plugin registering Evaluator Critic into the IoC container.
  - `def name() -> str`
  - `def version() -> str`
  - `def description() -> str`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def enable(context) -> None`
  - `def on_disable() -> None`
  - `def disable(context) -> None`


#### Functions

- `def critic_check_safety(command) -> dict[str, Any]`
  - Scan a shell command for dangerous, destructive, or irreversible operations.
- `def critic_evaluate_code(code, language) -> dict[str, Any]`
  - Statically analyze code syntax, metrics, and safety anti-patterns.
- `def critic_review_plan(goal, steps) -> dict[str, Any]`
  - Evaluate plan steps for completeness, verification, and risk mitigation.


### Module [`test_evaluator_critic.py`](test_evaluator_critic.py)

Tests for Evaluator Critic Adapter Plugin.

#### Functions

- `def test_adapter_tool_functions() -> None`
- `def test_evaluator_critic_plugin_lifecycle() -> None`



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
