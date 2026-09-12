# domain.agent_debater (v1.0.0)

Dialectical multi-agent reasoning, Proposer vs Challenger debate rounds, and arbiter verdict synthesizer

---

## Overview & Metadata

- **Plugin Directory**: `plugins/agent_orchestration/agent_debater`
- **Isolation Mode**: `in_process`
- **Services Provided**: `service.critic_evaluation`
- **Dependencies Required**: None

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `conduct_dialectical_debate` | `(topic, pro_arguments, con_arguments)` | Run structured dialectical debate rounds (Thesis / Proposer vs Antithesis / Challenger) |
| `synthesize_debate_verdict` | `(debate_summary)` | Synthesize final arbiter verdict, identifying concessions, unaddressed risks, and final recommendation |

---

## Key Modules & AST Symbols

### Module [`main.py`](main.py)

Dialectical Multi-Agent Debater & Arbiter Verdict Synthesis Plugin (Thin Adapter).

Delegates to the authoritative CriticEvaluationService seam while maintaining
100% backward-compatible function signatures and entrypoint contracts.

#### Classes

- `class AgentDebaterPlugin`
  Adapter plugin registering Agent Debater into the IoC container.
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

- `def conduct_dialectical_debate(topic, pro_arguments, con_arguments) -> dict[str, Any]`
  - Structure dialectical argument rounds between Proposer and Challenger.
- `def synthesize_debate_verdict(debate_summary) -> dict[str, Any]`
  - Synthesize an impartial arbiter decision based on debate rounds.


### Module [`test_agent_debater.py`](test_agent_debater.py)

Tests for Agent Debater Adapter Plugin.

#### Functions

- `def test_debater_tool_functions() -> None`
- `def test_agent_debater_plugin_lifecycle() -> None`



---

## Related Documentation & Configuration
- Manifest: [`plugin.json`](plugin.json)
- Architecture Seams: [Context Architecture](../../../CONTEXT-MAP.md) | [User Manual](../../../USER_MANUAL.md)
