# plugin.critic_loop (v1.0.0)

Authoritative critic, rubric evaluation, destructive command safety gate, and dialectical debate arbiter.

---

## Overview & Metadata

- **Plugin Directory**: `plugins/agent_orchestration/critic_loop`
- **Isolation Mode**: `in_process`
- **Services Provided**: `service.critic_evaluation`, `agent.critic_loop`
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `evaluate_rubric` | `(content, rubric)` | Evaluate draft text or code against a criteria checklist and produce itemized scoring |
| `run_critic_loop` | `(task, draft, threshold, max_iterations)` | Run iterative multi-turn critique and refinement until threshold score is achieved |
| `critic_check_safety` | `(command)` | Scan a CLI shell command for dangerous, destructive, or irreversible operations |
| `critic_evaluate_code` | `(code, language)` | Statically analyze code syntax, AST complexity, function docstrings, and potential anti-patterns |
| `critic_review_plan` | `(goal, steps)` | Evaluate an execution plan for verification steps, risks, and missing safeguards |
| `conduct_dialectical_debate` | `(topic, pro_arguments, con_arguments)` | Structure dialectical argument rounds between Proposer and Challenger |
| `synthesize_debate_verdict` | `(debate_summary)` | Synthesize an impartial arbiter decision based on debate rounds |

---

## Key Modules & AST Symbols

### Module [`main.py`](main.py)

Critic Evaluation & Safety Gatekeeper Plugin for Brain Harness.

Provides an authoritative, typed evaluation seam unifying:
1. Rubric scoring and heuristic criteria assessment
2. Destructive shell command screening
3. AST static code analysis and anti-pattern detection
4. Plan feasibility and risk mitigation review
5. Dialectical multi-agent debate and arbiter verdict synthesis
6. Autonomous generate-critique-revise loops

#### Classes

- `class CriticEvaluationService`
  Authoritative protocol for critic, safety evaluation, and dialectical debate.
  - `def evaluate_rubric(content, rubric) -> dict[str, Any]`
  - `def evaluate(content, rubric) -> dict[str, Any]`
  - `def check_command_safety(command) -> dict[str, Any]`
  - `def evaluate_code_ast(code, language) -> dict[str, Any]`
  - `def review_plan_feasibility(goal, steps) -> dict[str, Any]`
  - `def conduct_dialectical_debate(topic, pro_arguments, con_arguments) -> dict[str, Any]`
  - `def synthesize_debate_verdict(debate_summary) -> dict[str, Any]`
  - `def refine(task, draft) -> dict[str, Any]`
- `class CriticEvaluationServiceImpl`
  Consolidated implementation of the Critic & Safety Evaluation Gate.
  - `def evaluate(content, rubric) -> dict[str, Any]`
  - `def evaluate_rubric(content, rubric) -> dict[str, Any]`
  - `def check_command_safety(command) -> dict[str, Any]`
  - `def evaluate_code_ast(code, language) -> dict[str, Any]`
  - `def review_plan_feasibility(goal, steps) -> dict[str, Any]`
  - `def conduct_dialectical_debate(topic, pro_arguments, con_arguments) -> dict[str, Any]`
  - `def synthesize_debate_verdict(debate_summary) -> dict[str, Any]`
  - `def refine(task, draft) -> dict[str, Any]`
- `class CriticLoopPlugin`
  Authoritative plugin providing critic evaluation, safety gating, and dialectical debate.
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

- `def evaluate(content, rubric) -> dict[str, Any]`
- `def evaluate_rubric(content, rubric) -> dict[str, Any]`
- `def run_critic_loop(task, draft) -> dict[str, Any]`
- `def critic_check_safety(command) -> dict[str, Any]`
- `def critic_evaluate_code(code, language) -> dict[str, Any]`
- `def critic_review_plan(goal, steps) -> dict[str, Any]`
- `def conduct_dialectical_debate(topic, pro_arguments, con_arguments) -> dict[str, Any]`
- `def synthesize_debate_verdict(debate_summary) -> dict[str, Any]`


### Module [`test_critic_evaluation.py`](test_critic_evaluation.py)

Comprehensive tests for Critic & Safety Evaluation Gate Plugin.

#### Functions

- `def test_rubric_evaluation() -> None`
- `def test_command_safety_check() -> None`
- `def test_code_ast_evaluation() -> None`
- `def test_plan_feasibility_review() -> None`
- `def test_dialectical_debate_and_verdict() -> None`
- `def test_refinement_loop_convergence() -> None`
- `def test_critic_plugin_lifecycle_and_service_resolution() -> None`



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
