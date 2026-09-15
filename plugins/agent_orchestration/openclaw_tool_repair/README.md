# plugin.openclaw_tool_repair (v1.0.0)

In-flight stream normalization and plain-text tool-call recovery engine for repairing malformed LLM tool invocations.

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/agent_orchestration/openclaw_tool_repair` |
| Category | `agent_orchestration` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `openclaw_parse_tool_blocks` | `(text)` | Parses plain-text tool call codeblocks, JSON fences, or XML-wrapped calls from raw LLM output. |
| `openclaw_repair_tool_call` | `(raw_call, tool_name)` | Repairs malformed tool call JSON payloads (trailing commas, unescaped characters, unclosed brackets). |
| `openclaw_normalize_stream_chunk` | `(chunk)` | Processes a streaming chunk, stripping plain-text tool blocks from the visible stream and yielding promoted tool events. |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

OpenClaw Tool Repair Plugin — In-flight plain-text tool-call recovery and streaming event normalizer.

#### Classes

- `class OpenClawToolRepairServiceImpl` — AST regex parser and JSON repair engine implementing OpenClaw Tool Repair.
  - `def parse_plain_text_tool_blocks(text) -> list[OpenClawToolBlock]` — Parses model-emitted plain-text tool call blocks and code fences.
  - `def repair_json_call(raw_call) -> OpenClawToolBlock` — Repairs trailing commas, unbalanced brackets, and unescaped strings in JSON arguments.
  - `def normalize_stream_chunk(chunk) -> tuple[str, list[OpenClawToolBlock]]` — Filters stream chunks, stripping plain-text blocks and returning promoted tool events.
- `class OpenClawToolRepairPlugin` — Harness plugin registering OpenClaw Tool Repair service and tool entrypoints.
  - `def __init__() -> None`
  - `def register_services(context) -> None` — Register the typed OpenClawToolRepairService into the IoC container.
  - `def openclaw_parse_tool_blocks(text) -> list[dict[str, Any]]` — Tool handler for openclaw_parse_tool_blocks.
  - `def openclaw_repair_tool_call(raw_call, tool_name) -> dict[str, Any]` — Tool handler for openclaw_repair_tool_call.
  - `def openclaw_normalize_stream_chunk(chunk) -> dict[str, Any]` — Tool handler for openclaw_normalize_stream_chunk.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.openclaw_tool_repair.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
