"""MCP Client Plugin — connects external MCP servers into Harness.

Spawns an external MCP subprocess (e.g. `npx -y @modelcontextprotocol/server-filesystem`),
queries available tools via `tools/list`, and registers them as native tools in `ToolRegistry`.
"""

from __future__ import annotations

from typing import Any, cast

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
        self._discovered_resources: list[str] = []
        self._discovered_prompts: list[str] = []
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

        await self._discover_and_mount_resources()
        await self._discover_and_mount_prompts()

    async def on_disable(self) -> None:
        await self._unmount_resources_and_prompts()
        await self.unmount_tools()
        await self._stop_mcp_process()

    async def on_unload(self) -> None:
        await self._unmount_resources_and_prompts()
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
        try:
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
        except Exception as e:
            logger.debug("Failed discovering external MCP tools", provider=self.name, error=str(e))
            return []

    async def _discover_and_mount_resources(self) -> None:
        if not self._ctx:
            return
        from harness.mcp.protocol import MCPResource
        from harness.mcp.server import MCP_REGISTRY_KEY, MCPRegistry

        mcp_registry: MCPRegistry | None = self._ctx.optional(MCP_REGISTRY_KEY) if hasattr(self._ctx, "optional") else None
        if mcp_registry is None:
            return

        try:
            resp = await self._send_rpc("resources/list")
            resources = resp.get("result", {}).get("resources", [])
            for res_meta in resources:
                uri = res_meta.get("uri", "")
                name = res_meta.get("name", uri)
                desc = res_meta.get("description", "")
                mime = res_meta.get("mimeType", "application/json")

                target_uri = uri

                async def _make_handler() -> Any:
                    read_resp = await self._send_rpc("resources/read", {"uri": target_uri})
                    contents = read_resp.get("result", {}).get("contents", [])
                    if contents and isinstance(contents, list):
                        item = contents[0]
                        return item.get("text", item.get("blob", ""))
                    return read_resp.get("result", "")

                resource_obj = MCPResource(
                    uri=uri,
                    name=f"[{self.name}] {name}",
                    description=desc,
                    mime_type=mime,
                    handler=_make_handler,
                )
                mcp_registry.register_resource(resource_obj)
                self._discovered_resources.append(uri)

            if self._discovered_resources:
                logger.info("Mounted external MCP resources", count=len(self._discovered_resources), provider=self.name)
        except Exception as e:
            logger.debug("Failed discovering external MCP resources", provider=self.name, error=str(e))

    async def _discover_and_mount_prompts(self) -> None:
        if not self._ctx:
            return
        from harness.mcp.protocol import MCPPrompt
        from harness.mcp.server import MCP_REGISTRY_KEY, MCPRegistry

        mcp_registry: MCPRegistry | None = self._ctx.optional(MCP_REGISTRY_KEY) if hasattr(self._ctx, "optional") else None
        if mcp_registry is None:
            return

        try:
            resp = await self._send_rpc("prompts/list")
            prompts = resp.get("result", {}).get("prompts", [])
            for prompt_meta in prompts:
                name = prompt_meta.get("name", "")
                desc = prompt_meta.get("description", "")
                args = prompt_meta.get("arguments", [])
                target_name = name

                async def _make_template_handler(p_args: dict[str, Any]) -> list[dict[str, Any]]:
                    get_resp = await self._send_rpc("prompts/get", {"name": target_name, "arguments": p_args})
                    return cast(list[dict[str, Any]], get_resp.get("result", {}).get("messages", []))

                prompt_obj = MCPPrompt(
                    name=f"{self.name}.{name}",
                    description=desc,
                    arguments=args,
                    template_handler=_make_template_handler,
                )
                mcp_registry.register_prompt(prompt_obj)
                self._discovered_prompts.append(f"{self.name}.{name}")

            if self._discovered_prompts:
                logger.info("Mounted external MCP prompts", count=len(self._discovered_prompts), provider=self.name)
        except Exception as e:
            logger.debug("Failed discovering external MCP prompts", provider=self.name, error=str(e))

    async def _unmount_resources_and_prompts(self) -> None:
        if not self._ctx:
            return
        from harness.mcp.server import MCP_REGISTRY_KEY, MCPRegistry

        mcp_registry: MCPRegistry | None = self._ctx.optional(MCP_REGISTRY_KEY) if hasattr(self._ctx, "optional") else None
        if mcp_registry is not None:
            for uri in self._discovered_resources:
                mcp_registry.unregister_resource(uri)
            for pname in self._discovered_prompts:
                mcp_registry.unregister_prompt(pname)
        self._discovered_resources.clear()
        self._discovered_prompts.clear()

    def _make_tool_executor(self, remote_tool_name: str) -> Any:
        async def _exec(**kwargs: Any) -> Any:
            resp = await self._send_rpc(
                "tools/call",
                {"name": remote_tool_name, "arguments": kwargs},
            )
            return resp.get("result", resp.get("error"))

        return _exec
