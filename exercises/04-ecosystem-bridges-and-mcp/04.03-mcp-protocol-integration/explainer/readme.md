# Model Context Protocol (MCP) Bridge

## Overview

Brain Harness natively supports both consuming external MCP servers via `MCPClientPlugin` and serving Harness tools to external agent environments via `MCPServer`.

```
External Agent (Claude / Cursor) ◄──JSON-RPC──► Harness MCPServer (Exposes ToolRegistry)
                                                     │
Harness Kernel ◄──JSON-RPC──► External MCP Server (SQLite, Postgres, GitHub MCP)
```

```python
from harness.mcp.client_plugin import MCPClientPlugin

# Connect to an external MCP server (e.g. SQLite MCP)
client_plugin = MCPClientPlugin(
    server_name="sqlite_mcp",
    command=["npx", "-y", "@modelcontextprotocol/server-sqlite", "mydb.db"],
)
await client_plugin.on_load(ctx)
await client_plugin.on_enable()
# All MCP server tools are automatically bridged into Harness ToolRegistry!
```
