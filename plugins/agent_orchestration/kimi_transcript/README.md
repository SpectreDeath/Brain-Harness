# plugin.kimi_transcript (v1.0.0)

Isomorphic 4-layer transcript data engine with granularity-gated telemetry filtering and 4-tier DI scope hierarchy introspection.

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/agent_orchestration/kimi_transcript` |
| Category | `agent_orchestration` |
| Isolation Mode | `in_process` |
| Services Provided | None |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `kimi_transcript_project` | `(frames, granularity, cursor, limit)` | Projects raw or normalized agent execution event frames at client-requested granularity (off, turn, block, delta) with cursor pagination. |
| `kimi_scope_inspect` | `(depth_limit, include_services)` | Introspects the active ServiceContext parent-child hierarchy and annotates each context level with 4-tier scope roles (APP, WORKSPACE, SESSION, AGENT). |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

Kimi Transcript Plugin — Isomorphic 4-layer transcript data engine and 4-tier DI scope inspector.

#### Classes

- `class TranscriptProjectionEngine` — Isomorphic 4-layer projection engine filtering agent streams by client granularity.
  - `def normalize_frame(raw, default_turn) -> TranscriptFrame` — Coerce dict or frame into a normalized TranscriptFrame.
  - `def filter_by_granularity(frames, granularity) -> list[TranscriptFrame]` — Filter frames based on requested granularity: off, turn, block, delta.
  - `def project(raw_frames, granularity, cursor, limit) -> dict[str, Any]` — Project and paginate transcript frames.
- `class ScopeInspector` — Inspects ServiceContext hierarchy and infers 4-tier DI scope annotations.
  - `def inspect_context(context, depth_limit, include_services) -> list[ScopeAnnotation]` — Walk up or down the context tree and generate ScopeAnnotation models.
- `class KimiTranscriptServiceImpl` — Implementation of KimiTranscriptService providing projection and scope inspection.
  - `def __init__() -> None`
  - `def project_transcript(frames, granularity, cursor, limit) -> dict[str, Any]`
  - `def inspect_context_hierarchy(context) -> list[ScopeAnnotation]`
- `class KimiTranscriptPlugin` — Plugin providing isomorphic transcript streaming and 4-tier DI scope inspection.
  - `def __init__(service) -> None`
  - `def on_enable(context) -> None` — Register KimiTranscriptService into context.
  - `def on_disable(context) -> None` — Unregister service on disable.


#### Functions

- `def kimi_transcript_project(frames, granularity, cursor, limit) -> dict[str, Any]` — Projects raw event frames at client-requested granularity (off, turn, block, delta).
- `def kimi_scope_inspect(context, depth_limit, include_services) -> dict[str, Any]` — Introspects the active ServiceContext parent-child hierarchy with 4-tier scope roles.


---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.agent_orchestration.kimi_transcript.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
