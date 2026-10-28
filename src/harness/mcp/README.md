# Model Context Protocol (MCP) Integration (`harness.mcp`)

The `harness.mcp` package implements bidirectional integration with the Model Context Protocol (MCP). It supports both baseline standard MCP (`2024-11-05`, the industry standard) and forward-compatible scientific isolation extensions (`2026-07-28`, Rule 24), providing both an MCP server exposing Harness tools to external agent environments and an MCP client plugin discovering tools from external MCP servers.

---

## Architecture & Design

- **Protocol Versioning & Negotiation**: Negotiates protocol version between baseline `2024-11-05` and extended `2026-07-28`.
- **Stateless Scientific Tool Isolation (Rule 24)**: Heavy domain simulation engines and ODE solvers are encapsulated behind stateless MCP servers with strict JSONSchema validation.
- **`HarnessMCPServer`**: Serves active Harness tools, skill queries, and session management over Standard I/O and Streamable HTTP / SSE transports.
- **`MCPClientPlugin`**: Connects to external MCP servers, dynamically mapping remote tool schemas into local `ToolRegistry` entries.
- **`MCPProtocolCodec`**: Implements JSON-RPC 2.0 framing, error formatting, and bidirectionally parses requests, responses, and notification events.

---

## Key Modules

| Module | Core Classes | Responsibility |
|---|---|---|
| [`server.py`](server.py) | `HarnessMCPServer` | Host MCP server exposing tools, skills, and prompts over stdio or HTTP. |
| [`client_plugin.py`](client_plugin.py) | `MCPClientPlugin` | Client plugin importing tools from remote MCP servers into Harness. |
| [`protocol.py`](protocol.py) | `MCPProtocolCodec`, `MCPRequest` | JSON-RPC 2.0 protocol definitions, error codes, and serialization codec. |

---

## CLI Usage

Start the Harness MCP server over standard I/O:
```bash
harness mcp serve
```

Inspect tools registered on an external MCP server:
```bash
harness mcp tools --server "http://localhost:8080/mcp"
```

---

## Related Documentation
- [Tool Registry Service](../services/tools/registry.py)
- [CLI Commands Suite](../commands/mcp.py)
