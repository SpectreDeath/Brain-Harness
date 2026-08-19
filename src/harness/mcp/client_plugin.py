"""MCP Client Plugin — connects external MCP servers into Harness.

Spawns an external MCP subprocess (e.g. `npx -y @modelcontextprotocol/server-filesystem`),
queries available tools via `tools/list`, and registers them as native tools in `ToolRegistry`.
"""

from __future__ import annotations

from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.mcp.protocol import DEFAULT_PROTOCOL_VERSION, MCPProtocolCodec
from harness.plugins.base import HarnessPlugin
from harness.plugins.tool_mount import ToolMountMixin
from harness.plugins.transport import StdioJsonRpcTransport
from harness.services.tools import TOOL_REGISTRY_KEY, ToolSpec

logger = structlog.get_logger()


class MCPClientPlugin(ToolMountMixin, HarnessPlugin):
    """Bridge plugin connecting an external MCP server into Harness."""

    def __init__(
        self,
        name: str,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self._name = f"mcp.{name}"
        self._command = command
        self._args = args or []
        self._env = env
        self._transport: StdioJsonRpcTransport = StdioJsonRpcTransport(
            self._command,
            self._args,
            env=self._env,
        )
        self._discovered_tools: list[dict[str, Any]] = []
        self._ctx: ServiceContext | None = None
        self.codec = MCPProtocolCodec

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return f"External MCP Server client ({self._command})"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [ServiceKey(f"mcp.client.{self.name}")]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return [TOOL_REGISTRY_KEY]

    @property
    def trusted(self) -> bool:
        return True

    async def on_load(self, ctx: ServiceContext) -> None:
        self._ctx = ctx
        self.setup_tool_mount(ctx, self.name)

    async def on_enable(self) -> None:
        if not self._ctx:
            return

        await self._start_mcp_process()
        await self._initialize_mcp()
        specs = await self._discover_tool_specs()
        if specs:
            await self.mount_tools(specs)

    async def on_disable(self) -> None:
        await self.unmount_tools()
        await self._stop_mcp_process()

    async def on_unload(self) -> None:
        await self._stop_mcp_process()
        self.teardown_tool_mount()
        self._ctx = None

    async def _start_mcp_process(self) -> None:
        await self._transport.start()
        logger.info("External MCP process started", name=self.name, pid=self._transport.pid)

    async def _stop_mcp_process(self) -> None:
        await self._transport.stop()

    async def _send_rpc(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._transport.call(method, params)

    async def _initialize_mcp(self) -> None:
        await self._send_rpc(
            "initialize",
            {
                "protocolVersion": DEFAULT_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "harness-client", "version": "0.1.0"},
            },
        )

    async def _discover_tool_specs(self) -> list[ToolSpec]:
        resp = await self._send_rpc("tools/list")
        tools = resp.get("result", {}).get("tools", [])
        specs: list[ToolSpec] = []

        for tool_meta in tools:
            raw_tool_name = tool_meta.get("name", "")
            executor = self._make_tool_executor(raw_tool_name)
            spec = self.codec.mcp_tool_to_spec(
                tool_meta,
                provider=self.name,
                executor=executor,
            )
            specs.append(spec)

        logger.info("Discovered external MCP tools", count=len(specs), provider=self.name)
        return specs

    def _make_tool_executor(self, remote_tool_name: str) -> Any:
        async def _exec(**kwargs: Any) -> Any:
            resp = await self._send_rpc(
                "tools/call",
                {"name": remote_tool_name, "arguments": kwargs},
            )
            return resp.get("result", resp.get("error"))

        return _exec
