# domain.hermes_cognitive_engine (v1.0.0)

Hermes closed learning loop, autonomous skill formation, verification evidence evaluator, and think stream scrubber

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/agent_orchestration/hermes_cognitive_engine` |
| Category | `agent_orchestration` |
| Isolation Mode | `in_process` |
| Services Provided | `service.hermes_cognitive_engine` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `create_skill_from_trajectory` | `(trajectory_id, skill_name, domain, tool_sequence)` | Extract reusable multi-step tool call trajectory into an OpenSkills formatted skill |
| `evaluate_verification_evidence` | `(session_id, executed_commands, file_mutations)` | Evaluate pre-commit verification evidence (tests run, lint output, file mutations) before allowing completion |
| `scrub_think_stream` | `(raw_chunk, capture_telemetry)` | Parse streaming tokens to separate thinking blocks from user-visible response text and stream telemetry |
| `nudge_learning_persistence` | `(turn_count, complexity_score)` | Calculate cognitive nudge urgency for persisting extracted learnings based on turn count and complexity |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Hermes Cognitive Engine — learning loop, verification stop hooks, and think scrubbing.

#### Functions

- `def create_skill_from_trajectory(trajectory_id, skill_name, domain, tool_sequence) -> dict[str, Any]` — Synthesize an OpenSkills compliant skill from a successful tool execution trajectory.
- `def evaluate_verification_evidence(session_id, executed_commands, file_mutations) -> dict[str, Any]` — Inspect verification evidence to ensure edits were verified before turn completion.
- `def scrub_think_stream(raw_chunk, capture_telemetry) -> dict[str, Any]` — Parse reasoning tokens and separate internal thoughts from user-facing text.
- `def nudge_learning_persistence(turn_count, complexity_score) -> dict[str, Any]` — Calculate whether the agent should trigger an autobiographical persistence nudge.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.hermes_cognitive_engine.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
