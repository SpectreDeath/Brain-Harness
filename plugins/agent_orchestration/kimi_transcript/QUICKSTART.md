# Kimi Transcript Plugin (`plugin.kimi_transcript`)

The `plugin.kimi_transcript` brings Kimi Code's 4-layer isomorphic transcript streaming engine and 4-tier DI scope hierarchy inspector into Brain Harness.

## Features

1. **Granularity-Gated Transcript Projection (`kimi_transcript_project`)**:
   - Filter agent execution event streams according to client requirements:
     - `off`: Zero events (muted stream).
     - `turn`: Coarse turn boundaries (`user_input`, `agent_response`, `turn_complete`).
     - `block`: Atomic tool execution blocks (`tool_call`, `tool_result`, `checkpoint_saved`) and turns.
     - `delta`: Unfiltered streaming token deltas and real-time execution frames.
   - Built-in cursor pagination (`cursor`, `limit`, `has_more`, `next_cursor`).

2. **4-Tier DI Scope Inspection (`kimi_scope_inspect`)**:
   - Analyzes active `ServiceContext` parent-child trees without invasive kernel modifications.
   - Infers role boundaries: `APP` (Root) $\rightarrow$ `WORKSPACE` $\rightarrow$ `SESSION` $\rightarrow$ `AGENT`.

## Usage Recipes

### 1. Filter Token Stream for CLI/Dashboard Summary
```python
from plugins.agent_orchestration.kimi_transcript.main import kimi_transcript_project

events = [
    {"type": "user_input", "payload": {"text": "run tests"}},
    {"type": "token_delta", "payload": {"token": "Running"}},
    {"type": "tool_call", "payload": {"name": "pytest"}},
    {"type": "tool_result", "payload": {"output": "10 passed"}},
    {"type": "agent_response", "payload": {"text": "All tests passed."}},
]

# Block granularity strips token_delta but preserves tool blocks and turn text
result = await kimi_transcript_project(frames=events, granularity="block")
print(f"Projected {result['returned_count']} of {result['total_count']} events")
```

### 2. Inspect DI Scopes
```python
from plugins.agent_orchestration.kimi_transcript.main import kimi_scope_inspect
from harness.kernel.context import ServiceContext

root = ServiceContext()
workspace = root.child()
session = workspace.child()
agent = session.child()

report = await kimi_scope_inspect(context=agent)
for scope in report["scopes"]:
    print(f"Depth {scope['depth']}: {scope['scope_type'].upper()} ({scope['active_count']} services)")
```
