"""MCP request context, typed service keys, and handler type definitions (Rule 2 & Rule 12)."""

from __future__ import annotations

import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from harness.kernel.context import ServiceKey
from harness.mcp.protocol import MCPProtocolCodec

if TYPE_CHECKING:
    from harness.mcp.server.registry import MCPRegistry

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

MCP_REGISTRY_KEY: ServiceKey[MCPRegistry] = ServiceKey("mcp.registry")


@dataclass(slots=True)
class MCPRequestContext:
    """Execution context for an MCP request passed through the method router and interceptors."""

    request_id: Any | None
    method: str
    params: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    event_bus: Any | None = None
    codec: type[MCPProtocolCodec] = MCPProtocolCodec


# Route Handler Type
MCPHandler = Callable[[dict[str, Any], MCPRequestContext], Awaitable[dict[str, Any]]]

__all__ = [
    "MCPHandler",
    "MCPRequestContext",
    "MCP_REGISTRY_KEY",
]
