# domain.antigravity_otel_telemetry (v1.0.0)

Google Antigravity OpenTelemetry distributed trace exporter and dynamic CLI statusline IPC metric generator

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/data_engineering/antigravity_otel_telemetry` |
| Category | `data_engineering` |
| Isolation Mode | `in_process` |
| Services Provided | `service.antigravity.telemetry` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `start_telemetry_span` | `(name, span_id, parent_id)` | Start a new hierarchical telemetry span |
| `end_telemetry_span` | `(span_id, status)` | Close an active telemetry span |
| `get_statusline_payload` | `(mode)` | Generate Antigravity dynamic statusline IPC payload |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Antigravity OTel Telemetry Entrypoints.

#### Functions

- `def start_telemetry_span(name, span_id, parent_id) -> dict[str, Any]` — Start a new hierarchical telemetry span.
- `def end_telemetry_span(span_id, status) -> dict[str, Any]` — Close an active telemetry span.
- `def get_statusline_payload(mode) -> dict[str, Any]` — Generate Antigravity dynamic statusline IPC payload.

### Module [__init__.py](__init__.py)

Antigravity OTel Telemetry Plugin Package.
### Module [service.py](service.py)

Google Antigravity OpenTelemetry Distributed Tracing & Statusline IPC Service Implementation.

#### Classes

- `class SpanRecord`
- `class AntigravityTelemetryService` — Authoritative distributed tracing and CLI statusline telemetry service.
  - `def __init__() -> None`
  - `def start_span(name, span_id, parent_id, attributes) -> SpanRecord` — Start a new hierarchical telemetry span.
  - `def end_span(span_id, status, extra_attributes) -> SpanRecord | None` — Close an active telemetry span with duration calculation.
  - `def record_tokens(prompt_tokens, completion_tokens) -> None` — Accumulate token consumption.
  - `def export_statusline_payload(mode) -> dict[str, Any]` — Generate Antigravity dynamic statusline IPC payload.
  - `def list_spans() -> list[SpanRecord]`
- `class AntigravityOtelTelemetryPlugin` — In-process Harness plugin providing Antigravity telemetry service.
  - `def __init__() -> None`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None`
  - `def on_enable() -> None`
  - `def on_disable() -> None`
  - `def on_unload() -> None`


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.data_engineering.antigravity_otel_telemetry.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
