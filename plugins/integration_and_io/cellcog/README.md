# plugin.cellcog (v1.0.0)

Any-to-any multimodal sub-agent delegation via CellCog SDK — research, media, documents, code

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/integration_and_io/cellcog` |
| Category | `integration_and_io` |
| Isolation Mode | `subprocess` |
| Services Provided | `service.cellcog` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `cellcog_run` | `(prompt, chat_mode, chat_tier, timeout, task_label)` | Execute any-to-any multimodal task via CellCog (agent or creative mode) |
| `cellcog_research` | `(topic, attachments, chat_tier, timeout)` | Deep multi-source research synthesis via CellCog team mode |
| `cellcog_list_capabilities` | `()` | List available CellCog modality skills and their categories |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

CellCog Multimodal Sub-Agent Plugin for Brain Harness.

#### Classes

- `class CellCogPlugin` — Brain Harness plugin for CellCog any-to-any sub-agent delegation.
  - `def __init__(service) -> None`
  - `def name() -> str`
  - `def version() -> str`
  - `def description() -> str`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None` — Register the CellCog service in the IoC container and link EventBus if available.
  - `def on_enable() -> None` — Start CellCog plugin operations.
  - `def on_disable() -> None` — Pause CellCog plugin operations.
  - `def on_unload() -> None` — Clean up CellCog plugin resources.


#### Functions

- `def cellcog_run(prompt, chat_mode, chat_tier, timeout, task_label) -> dict[str, Any]` — Execute an any-to-any multimodal task via CellCog.
- `def cellcog_research(topic, attachments, chat_tier, timeout) -> dict[str, Any]` — Execute deep multi-source research via CellCog team mode.
- `def cellcog_list_capabilities() -> dict[str, Any]` — List available CellCog modality capabilities and their categories.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.integration_and_io.cellcog.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `subprocess` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
