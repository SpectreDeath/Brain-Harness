# Harness UI Dashboard & Telemetry Projection (`harness.ui`)

The `harness.ui` package provides the FastAPI web dashboard, real-time WebSocket telemetry stream broadcaster, and REST management endpoints for Brain Harness.

---

## Central Function & Capabilities

The UI package provides both interactive visual monitoring and machine-readable streaming:
1. **Interactive Control Dashboard**: Single-page application serving live plugin lifecycle controls, dynamic Mermaid dependency graphs, tool inspection, and agent execution interfaces.
2. **Real-Time WebSocket Streaming**: Bi-directional WebSocket channels broadcasting live events (`/ws/events`), step updates, and swarm execution trees.
3. **Telemetry Projection Engine**: The `UIProjectionEngine` filters, buffers, and projects raw event bus streams into client channels (`events`, `agent`, `swarm`, `metrics`, `system`).
4. **REST API Endpoints**: Full programmatic control surface for headless execution, automated health checks, task execution, and plugin toggling.

---

## Key Modules & Symbols

| Module | Core Classes / Symbols | Description |
|---|---|---|
| [`server.py`](server.py) | `create_app`, `RuntimeAdapter`, `TaskRequest` | FastAPI application factory defining REST and WebSocket routes for runtime interaction. |
| [`projection.py`](projection.py) | `UIProjectionEngine`, `ChannelSubscription` | Decoupled telemetry engine filtering and routing events across active WebSocket clients. |

---

## Core API & WebSocket Endpoints

| Endpoint | Method / Protocol | Description |
|---|---|---|
| `/` | `GET` | Single-page responsive control dashboard HTML interface. |
| `/api/health` | `GET` | Health check and active runtime status report. |
| `/api/plugins` | `GET` / `POST` | List registered plugins and toggle enabled/disabled states. |
| `/api/agent/run` | `POST` | Dispatch an autonomous task to the ReAct agent execution engine. |
| `/api/graph` | `GET` | Return live Mermaid diagram representing kernel plugin dependencies. |
| `/ws/events` | `WebSocket` | Real-time streaming channel for system events and agent observations. |

---

## Programmatic Server Launch Example

```python
import uvicorn
from harness.kernel.runtime import HarnessRuntime
from harness.ui.server import create_app

async def launch_dashboard():
    async with HarnessRuntime.create() as runtime:
        app = create_app(runtime)
        config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

if __name__ == "__main__":
    import asyncio
    asyncio.run(launch_dashboard())
```

---

## Related Documentation

- [User Manual](../../../USER_MANUAL.md)
- [CLI Reference](../../../docs/reference/cli.md)
- [Event Bus Architecture](../events/README.md)
- [Agent Execution](../agent/README.md)
