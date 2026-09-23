# FastMCP Universal Adapter Pattern & JSON-RPC Client-Server Transport Seams

**ID:** `ki_hf_fastmcp_dynamic_tool_protocol`  
**Category:** `integration_and_io`  
**Origin:** *The Context Course: Unit 2 (MCP)* (Hugging Face)  
**Provenance Lineage:** Units 2.1-2.4, Hugging Face, 2026.

## Executive Summary

Before the Model Context Protocol (MCP), connecting $M$ agent harnesses to $N$ external systems required $M \times N$ bespoke integration libraries. MCP eliminates this bottleneck by standardizing client-host-server interactions over JSON-RPC 2.0. Agents function as MCP Clients; external data stores and computational engines operate as MCP Servers.

### The Three MCP Capability Primitives
1. **Tools**: Callable functions with JSON Schema parameters executed on behalf of the agent (e.g. database queries, GitHub PR creation, model inference).
2. **Resources**: Passive, read-only data assets URI-identified (e.g. `file:///`, `postgres://`) that agents can inspect or subscribe to for change notifications.
3. **Prompts**: Pre-engineered prompt templates parameterized with dynamic context and served to the agent.

### Transports & FastMCP Engine
FastMCP simplifies server creation via high-level decorators (`@mcp.tool()`, `@mcp.resource()`). MCP supports two foundational transport modes:
- **Stdio Transport**: Child process spawning communicating via standard input/output pipes. Ideal for local sandboxed tools and private CLI utilities.
- **Server-Sent Events (SSE) / HTTP Transport**: Asynchronous streaming transport over network endpoints. Enables cloud-hosted tool services and multi-agent shared infrastructure (e.g., Gradio Spaces exposing live ML inference as MCP tools).

## Operational Deployment Invariants

1. **Strict Docstring & Type Hint Contract**: FastMCP synthesizes JSON Schema directly from Python type annotations and docstrings. Missing docstrings or vague types (`Any`) degrade model tool-calling accuracy.
2. **Subprocess Pipe Drainage**: When running stdio MCP servers, proactor event loops must explicitly drain standard streams in `finally` blocks to prevent deadlocks (Rule 14).
3. **Gradio MCP Bridge**: Visual Gradio apps can dual-mount as FastMCP servers (`gr.mount_mcp(app)`), enabling humans to interact via GUI while autonomous agents invoke backend functions via JSON-RPC.
