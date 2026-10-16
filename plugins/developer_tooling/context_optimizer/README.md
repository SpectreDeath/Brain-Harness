# plugin.context_optimizer (v1.0.0)

Pre-LLM context optimization, observation compaction, and composable pruning strategies

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/developer_tooling/context_optimizer` |
| Category | `developer_tooling` |
| Isolation Mode | `in_process` |
| Services Provided | `service.context_optimizer`, `agent.context_optimizer` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `context_compact_observation` | `(action_name, observation, max_chars)` | Compact raw tool observation into a token-efficient string. |
| `context_optimize_messages` | `(messages, max_total_messages, recent_messages_preserve)` | Prune message sequence using registered optimization strategies. |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Pre-LLM context optimization, observation compaction, and composable pruning strategies

#### Classes

- `class ContextOptimizerPlugin` — Plugin providing pre-LLM context optimization, observation compaction, and strategy pipelines.
  - `def __init__(config)` — Executes the operation.
  - `def name()` — Executes the operation.
  - `def version()` — Executes the operation.
  - `def description()` — Executes the operation.
  - `def provides()` — Executes the operation.
  - `def requires()` — Executes the operation.
  - `def on_load(context)` — Register the service into the micro-kernel IoC container (Rule 1 & Rule 2).
  - `def enable(context)` — Executes the operation.
  - `def on_disable()` — Executes the operation.
  - `def disable(context)` — Executes the operation.
  - `def compact_observation(action_name, observation, max_chars)` — Executes the operation.
  - `def optimize_messages(messages, config)` — Executes the operation.

---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.developer_tooling.context_optimizer.main import plugin

context = ServiceContext()
# Load plugin into service context
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
