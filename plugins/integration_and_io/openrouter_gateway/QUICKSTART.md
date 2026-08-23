# OpenRouter Gateway Plugin (`plugin.openrouter_gateway`)

The `plugin.openrouter_gateway` synthesizes OpenRouter routing logic and JSON-RPC 2.0 protocol dispatching extracted from Kilo Code (`packages/kilo-gateway` and `packages/opencode`).

## Features
- **Typed IoC Service:** Registered under `ServiceKey[OpenRouterGatewayService]("service.openrouter_gateway")`.
- **JSON-RPC 2.0 Engine:** Supports `openrouter.chat`, `openrouter.models`, `openrouter.route`, and batch execution.
- **Context Epoch KV-Cache Optimization (`KI-KILO-01`):** Formats immutable root system prompts and appends chronological mid-conversation system updates to maximize prefix caching.
- **Header Attribution:** Injects `X-KiloCode-*` tracking headers for task attribution, feature tracking, and tester suppression.

## Configuration
Set either environment variable:
```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
# or
export KILO_API_KEY="kilo_..."
```

Optional settings:
```bash
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
export KILOCODE_ORGANIZATIONID="org_123"
export KILOCODE_FEATURE="agent_harness"
```

## Python Integration Example

```python
from harness.kernel.context import ServiceContext
from plugins.integration_and_io.openrouter_gateway.service import (
    OPENROUTER_GATEWAY_KEY,
    OpenRouterGatewayService,
)

# 1. Resolve service from context
gateway: OpenRouterGatewayService = ctx.require(OPENROUTER_GATEWAY_KEY)

# 2. Execute chat completion with reasoning effort
response = await gateway.chat(
    messages=[{"role": "user", "content": "Write a topological sort in Python"}],
    model="anthropic/claude-3.7-sonnet",
    reasoning={"effort": "high"},
    order=["Anthropic", "Together"],
)

print(response.content)
```

## JSON-RPC 2.0 Example

```json
{
  "jsonrpc": "2.0",
  "method": "openrouter.chat",
  "params": {
    "model": "anthropic/claude-3.7-sonnet",
    "messages": [
      {"role": "user", "content": "Hello via JSON-RPC!"}
    ]
  },
  "id": "req-001"
}
```
