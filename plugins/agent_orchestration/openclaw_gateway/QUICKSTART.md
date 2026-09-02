# OpenClaw Gateway Plugin Quickstart

The `plugin.openclaw_gateway` connects Brain Harness agents to local or remote OpenClaw Gateway instances over WebSocket JSON-RPC.

## Key Capabilities

1. **`openclaw_gateway_connect`**: Authenticates and establishes JSON-RPC connection with Gateway.
2. **`openclaw_gateway_list_sessions`**: Inspects active session trees and channel connections.
3. **`openclaw_gateway_create_session`**: Allocates a new session placement on Gateway with custom permissions (`auto`, `prompt`, `strict`, `read_only`).
4. **`openclaw_gateway_call_tool`**: Dispatches tool executions through OpenClaw tool runtimes.
5. **`openclaw_gateway_send_message`**: Sends routed messages to external chat channels (Slack, Discord, Telegram, etc.).

## Example Agent Invocation

```python
from harness.kernel.context import ServiceContext
from harness.services.openclaw_bridge import OPENCLAW_GATEWAY_KEY

gateway = context.resolve(OPENCLAW_GATEWAY_KEY)
await gateway.connect("ws://127.0.0.1:18789", token="my_token")
session = await gateway.create_session(channel="slack", permission_mode="prompt")
result = await gateway.call_tool(session.session_id, "calculator", {"expression": "42 * 10"})
```
