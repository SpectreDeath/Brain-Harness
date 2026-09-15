# plugin.openrouter_gateway (v1.0.0)

OpenRouter Gateway routing, JSON-RPC 2.0 protocol engine, and Context Epoch prompt optimizer

---

## Overview & Metadata

| Property | Value |
|---|---|
| Plugin Directory | `plugins/integration_and_io/openrouter_gateway` |
| Category | `integration_and_io` |
| Isolation Mode | `in_process` |
| Services Provided | `service.openrouter_gateway` |
| Dependencies Required | None |

---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `openrouter_chat` | `(messages, model, reasoning, temperature, max_tokens, order, allow_fallbacks, api_key, task_id, feature)` | Execute chat completion via OpenRouter / Kilo Gateway with model routing and reasoning controls |
| `openrouter_list_models` | `(provider, modality, max_price, api_key)` | Fetch and filter available models from OpenRouter catalogue |
| `openrouter_resolve_route` | `(task_type, tier, budget)` | Intelligently match task complexity and tier to optimal OpenRouter model routes |
| `openrouter_jsonrpc_call` | `(request_payload, api_key)` | Execute direct JSON-RPC 2.0 protocol request against OpenRouter Gateway |

---

## Key Modules & AST Symbols

### Module [main.py](main.py)

OpenRouter Gateway Plugin for Brain Harness.

Provides OpenRouter endpoint routing, JSON-RPC 2.0 protocol dispatching,
and Context Epoch KV-cache optimization extracted from Kilo Code.

#### Classes

- `class OpenRouterGatewayPlugin` — Brain Harness plugin for OpenRouter model routing and JSON-RPC 2.0 dispatch.
  - `def __init__(service) -> None`
  - `def name() -> str`
  - `def version() -> str`
  - `def description() -> str`
  - `def provides() -> list[ServiceKey[Any]]`
  - `def requires() -> list[ServiceKey[Any]]`
  - `def on_load(ctx) -> None` — Register the typed service instance in the IoC container.
  - `def on_enable() -> None` — Lifecycle hook when plugin is enabled.
  - `def on_disable() -> None` — Lifecycle hook when plugin is disabled.
  - `def on_unload() -> None` — Clean up resources on unload.


#### Functions

- `def openrouter_chat(messages, model, reasoning, temperature, max_tokens, order, allow_fallbacks, api_key, task_id, feature) -> dict[str, Any]` — Execute chat completion via OpenRouter / Kilo Gateway with model routing.
- `def openrouter_list_models(provider, modality, max_price, api_key) -> dict[str, Any]` — Fetch and filter available models from OpenRouter catalogue.
- `def openrouter_resolve_route(task_type, tier, budget) -> dict[str, Any]` — Intelligently match task complexity and tier to optimal OpenRouter model routes.
- `def openrouter_jsonrpc_call(request_payload, api_key) -> dict[str, Any]` — Execute direct JSON-RPC 2.0 protocol request against OpenRouter Gateway.

### Module [headers.py](headers.py)

Header construction and metadata attribution for OpenRouter Gateway.

Ported and extended from Kilo Code's packages/kilo-gateway/src/headers.ts.
Provides fine-grained request attribution, task tracing, and tester suppression.

#### Functions

- `def get_user_agent() -> str` — Return configured or default User-Agent string.
- `def get_editor_name_header() -> str` — Return editor name identifier.
- `def get_feature_header() -> str | None` — Return active feature tag from environment if set.
- `def build_kilo_headers(task_id, parent_task_id, project_id, organization_id, feature, tester_warnings_disabled_until, machine_id, custom_headers) -> dict[str, str]` — Construct standard attribution headers for OpenRouter / Kilo Gateway requests.

### Module [service.py](service.py)

OpenRouter Gateway service backwards compatibility shim.

Canonical service definition and models are located at `harness.services.openrouter_gateway`.

---

## Quickstart & Usage

```python
from harness.kernel.context import ServiceContext
from plugins.integration_and_io.openrouter_gateway.main import plugin

# Load plugin into harness service context
context = ServiceContext()
plugin.on_load(context)
```

---

## Architecture & Diátaxis Classification

- Diátaxis Quadrant: Reference (Track B) & How-To Guides
- Isolation: `in_process` execution sandbox
- Invariants: Slotted dataclass architecture (Rule 12), transactional context bounds (Rule 8), and zero-fork YAML configuration (Rule 44).
