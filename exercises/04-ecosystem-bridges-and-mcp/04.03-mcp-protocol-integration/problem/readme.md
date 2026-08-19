# Problem: Host Harness Tools via MCP Server

## Objective

Initialize a `ToolRegistry`, register a tool, initialize `MCPServer`, and verify the `tools/list` JSON-RPC endpoint.

## Tasks

1. Register `"system.ping"` in `ToolRegistry`.
2. Instantiate `MCPServer(tools=registry)`.
3. Handle request `{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}`.
4. Verify tool presence in response.
