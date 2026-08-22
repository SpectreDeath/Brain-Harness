"""MCP (Model Context Protocol) STDIO server and method router for Harness.

Exposes all registered Harness tools, resources, and execution surfaces to any MCP client
(such as Claude Desktop, VS Code, Cursor, or external orchestrators) via STDIO or JSON-RPC.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import sys
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

import structlog

from harness.mcp.protocol import (
    JSONRPC_INTERNAL_ERROR,
    JSONRPC_METHOD_NOT_FOUND,
    JSONRPC_PARSE_ERROR,
    MCPNotification,
    MCPPrompt,
    MCPProtocolCodec,
    MCPResource,
)
from harness.kernel.context import ServiceKey
from harness.services.tools import ToolRegistry

logger = structlog.get_logger()

MCP_REGISTRY_KEY: ServiceKey[MCPRegistry] = ServiceKey("mcp.registry")


@dataclass
class MCPRequestContext:
    """Execution context for an MCP request passed through the method router and interceptors."""

    request_id: Any | None
    method: str
    params: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    event_bus: Any | None = None
    codec: type[MCPProtocolCodec] = MCPProtocolCodec


class MCPInterceptor(ABC):
    """Abstract middleware interceptor for MCP request pipeline."""

    @abstractmethod
    async def intercept(
        self,
        ctx: MCPRequestContext,
        next_handler: Callable[[MCPRequestContext], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        """Wrap, inspect, or modify MCP request execution."""


class MCPTelemetryInterceptor(MCPInterceptor):
    """Emits telemetry events for MCP requests and responses when event_bus is present."""

    async def intercept(
        self,
        ctx: MCPRequestContext,
        next_handler: Callable[[MCPRequestContext], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        if ctx.event_bus:
            from harness.events.types import EventType, HarnessEvent

            req_event = HarnessEvent(
                event_type=EventType.CUSTOM,
                source="mcp.server",
                payload={"method": ctx.method, "id": ctx.request_id, "stage": "request"},
            )
            try:
                await ctx.event_bus.emit(req_event)
            except Exception:
                pass

        resp = await next_handler(ctx)

        if ctx.event_bus:
            from harness.events.types import EventType, HarnessEvent

            is_error = "error" in resp
            res_event = HarnessEvent(
                event_type=EventType.CUSTOM,
                source="mcp.server",
                payload={
                    "method": ctx.method,
                    "id": ctx.request_id,
                    "stage": "error" if is_error else "response",
                    "error": resp.get("error") if is_error else None,
                },
            )
            try:
                await ctx.event_bus.emit(res_event)
            except Exception:
                pass

        return resp


class MCPAccessControlInterceptor(MCPInterceptor):
    """Enforces allowed methods or client origin authorization policies."""

    def __init__(self, allowed_methods: set[str] | None = None) -> None:
        self.allowed_methods = allowed_methods

    async def intercept(
        self,
        ctx: MCPRequestContext,
        next_handler: Callable[[MCPRequestContext], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        if self.allowed_methods is not None and ctx.method not in self.allowed_methods:
            return ctx.codec.encode_error(
                ctx.request_id,
                code=-32001,
                message=f"Access denied: method '{ctx.method}' is not permitted by policy",
            )
        return await next_handler(ctx)


class MCPInterceptorPipeline:
    """Composes interceptors into a single onion execution chain for MCP requests."""

    def __init__(self, interceptors: list[MCPInterceptor] | None = None) -> None:
        self._interceptors: list[MCPInterceptor] = list(interceptors or [])

    def add_interceptor(self, interceptor: MCPInterceptor) -> None:
        """Append an interceptor to the end of the pipeline."""
        self._interceptors.append(interceptor)

    async def execute(
        self,
        ctx: MCPRequestContext,
        terminal_handler: Callable[[MCPRequestContext], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        """Execute request context through all interceptors before calling terminal handler."""
        if not self._interceptors:
            return await terminal_handler(ctx)

        async def _dispatch(idx: int, current_ctx: MCPRequestContext) -> dict[str, Any]:
            if idx >= len(self._interceptors):
                return await terminal_handler(current_ctx)

            interceptor = self._interceptors[idx]

            async def _next(next_ctx: MCPRequestContext) -> dict[str, Any]:
                return await _dispatch(idx + 1, next_ctx)

            return await interceptor.intercept(current_ctx, _next)

        return await _dispatch(0, ctx)


class MCPRegistry:
    """Authoritative registry for MCP tools, resources, and prompt templates."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        *,
        context: Any | None = None,
        loader: Any | None = None,
    ) -> None:
        self.tool_registry = tool_registry
        self.context = context
        self.loader = loader
        self._custom_resources: dict[str, MCPResource] = {}
        self._custom_prompts: dict[str, MCPPrompt] = {}

    def register_resource(self, resource: MCPResource) -> None:
        """Register a custom MCP resource."""
        self._custom_resources[resource.uri] = resource

    def unregister_resource(self, uri: str) -> bool:
        """Unregister a custom MCP resource by URI."""
        return self._custom_resources.pop(uri, None) is not None

    def register_prompt(self, prompt: MCPPrompt) -> None:
        """Register a custom MCP prompt template."""
        self._custom_prompts[prompt.name] = prompt

    def unregister_prompt(self, name: str) -> bool:
        """Unregister a custom MCP prompt template by name."""
        return self._custom_prompts.pop(name, None) is not None

    def list_resources(self) -> list[dict[str, Any]]:
        """List all available MCP resources."""
        resources: list[dict[str, Any]] = [
            {
                "uri": "harness://plugins/catalog",
                "name": "Harness Plugin Catalog",
                "description": "Complete catalog of installed and cached plugins",
                "mimeType": "application/json",
            },
            {
                "uri": "harness://system/status",
                "name": "Harness System Diagnostics",
                "description": "Live active services and tool provider mappings",
                "mimeType": "application/json",
            },
        ]
        if self.loader is not None:
            catalog = self.loader.list_catalog()
            for item in catalog:
                p_name = item.get("name", "")
                resources.append({
                    "uri": f"harness://plugins/{p_name}/guide",
                    "name": f"{p_name} Quickstart Guide",
                    "description": item.get("description", f"Guide for {p_name}"),
                    "mimeType": "text/markdown",
                })
        for res in self._custom_resources.values():
            resources.append(res.to_dict())
        return resources

    async def read_resource(self, uri: str) -> tuple[Any, str] | None:
        """Read resource content and return (content, mime_type) or None if not found."""
        if uri in self._custom_resources:
            res = self._custom_resources[uri]
            if res.handler is not None:
                content = res.handler()
                if inspect.isawaitable(content):
                    content = await content
                return content, res.mime_type
            return res.description, res.mime_type

        if uri == "harness://plugins/catalog":
            catalog_data = self.loader.list_catalog() if self.loader else []
            return catalog_data, "application/json"

        if uri == "harness://system/status":
            status_data: dict[str, Any] = {
                "tools_count": len(self.tool_registry.list_tools()),
                "tools": [t.name for t in self.tool_registry.list_tools()],
            }
            if self.context and hasattr(self.context, "list_services"):
                status_data["services"] = self.context.list_services()
            return status_data, "application/json"

        if uri.startswith("harness://plugins/") and uri.endswith("/guide"):
            plugin_name = uri.split("harness://plugins/")[1].split("/guide")[0]
            guide_content = f"# Plugin: {plugin_name}\n\nPlugin documentation not available."
            if self.loader:
                guide_res = self.loader.get_guide(plugin_name)
                if guide_res:
                    _, guide_content = guide_res
            return guide_content, "text/markdown"

        return None

    def list_prompts(self) -> list[dict[str, Any]]:
        """List all available MCP prompts."""
        prompts = [
            {
                "name": "agent_task",
                "description": "Autonomous ReAct task execution prompt",
                "arguments": [
                    {"name": "task", "description": "Task description", "required": True}
                ],
            },
            {
                "name": "plugin_review",
                "description": "Inspect and audit plugin capabilities",
                "arguments": [
                    {"name": "plugin_name", "description": "Name of plugin", "required": True}
                ],
            },
        ]
        for p in self._custom_prompts.values():
            prompts.append(p.to_dict())
        return prompts

    async def get_prompt(
        self, name: str, arguments: dict[str, Any]
    ) -> tuple[str, list[dict[str, Any]]] | None:
        """Return (description, messages) or None if not found."""
        if name in self._custom_prompts:
            prompt = self._custom_prompts[name]
            if prompt.template_handler is not None:
                msgs = prompt.template_handler(arguments)
                if inspect.isawaitable(msgs):
                    msgs = await msgs
                return prompt.description, msgs
            return prompt.description, [
                {"role": "user", "content": {"type": "text", "text": prompt.description}}
            ]

        if name == "agent_task":
            task_text = arguments.get("task", "Execute task")
            return "Autonomous ReAct task execution prompt", [
                {"role": "user", "content": {"type": "text", "text": f"Solve this task using tools: {task_text}"}}
            ]

        if name == "plugin_review":
            pname = arguments.get("plugin_name", "plugin")
            return "Inspect and audit plugin capabilities", [
                {"role": "user", "content": {"type": "text", "text": f"Analyze and audit plugin '{pname}'."}}
            ]

        return None


# Route Handler Type
MCPHandler = Callable[[dict[str, Any], MCPRequestContext], Awaitable[dict[str, Any]]]


class MCPMethodRouter:
    """Authoritative method router for dispatching JSON-RPC 2.0 MCP requests."""

    def __init__(
        self,
        registry: MCPRegistry,
        *,
        pipeline: MCPInterceptorPipeline | None = None,
        codec: type[MCPProtocolCodec] = MCPProtocolCodec,
    ) -> None:
        self.registry = registry
        self.pipeline = pipeline or MCPInterceptorPipeline()
        self.codec = codec
        self._handlers: dict[str, MCPHandler] = {}
        self._register_default_routes()

    def register(self, method: str, handler: MCPHandler) -> None:
        """Register a handler for a specific JSON-RPC method."""
        self._handlers[method] = handler

    def has_route(self, method: str) -> bool:
        """Check if a route handler exists for a method."""
        return method in self._handlers

    def _register_default_routes(self) -> None:
        """Register default MCP handlers."""

        async def _handle_initialize(params: dict[str, Any], ctx: MCPRequestContext) -> dict[str, Any]:
            return self.codec.build_initialize_response(
                ctx.request_id,
                server_name="harness-mcp",
                version="0.1.0",
            )

        async def _handle_ping(params: dict[str, Any], ctx: MCPRequestContext) -> dict[str, Any]:
            return self.codec.encode_response(ctx.request_id, {})

        async def _handle_tools_list(params: dict[str, Any], ctx: MCPRequestContext) -> dict[str, Any]:
            tools_list = self.registry.tool_registry.to_mcp_tools(enabled_only=False)
            return self.codec.build_tools_list_response(ctx.request_id, tools_list)

        async def _handle_tools_call(params: dict[str, Any], ctx: MCPRequestContext) -> dict[str, Any]:
            tool_name = str(params.get("name", ""))
            arguments = params.get("arguments", {})
            if not isinstance(arguments, dict):
                arguments = {}

            result = await self.registry.tool_registry.invoke(tool_name, arguments)
            is_error = result.get("status") == "error"
            content_payload = result.get("result", result.get("error", "done"))

            return self.codec.build_tool_call_response(
                ctx.request_id,
                result=content_payload,
                is_error=is_error,
            )

        async def _handle_resources_list(params: dict[str, Any], ctx: MCPRequestContext) -> dict[str, Any]:
            resources = self.registry.list_resources()
            return self.codec.build_resources_list_response(ctx.request_id, resources)

        async def _handle_resources_read(params: dict[str, Any], ctx: MCPRequestContext) -> dict[str, Any]:
            uri = str(params.get("uri", ""))
            res_result = await self.registry.read_resource(uri)
            if res_result is not None:
                content, mime = res_result
                return self.codec.build_resource_read_response(
                    ctx.request_id, uri, content, mime_type=mime
                )

            return self.codec.encode_error(
                ctx.request_id,
                code=-32602,
                message=f"Resource not found: {uri}",
            )

        async def _handle_prompts_list(params: dict[str, Any], ctx: MCPRequestContext) -> dict[str, Any]:
            prompts = self.registry.list_prompts()
            return self.codec.build_prompts_list_response(ctx.request_id, prompts)

        async def _handle_prompts_get(params: dict[str, Any], ctx: MCPRequestContext) -> dict[str, Any]:
            prompt_name = str(params.get("name", ""))
            arguments = params.get("arguments", {})
            prompt_result = await self.registry.get_prompt(prompt_name, arguments)
            if prompt_result is not None:
                desc, messages = prompt_result
                return self.codec.build_prompt_get_response(
                    ctx.request_id,
                    description=desc,
                    messages=messages,
                )

            return self.codec.encode_error(
                ctx.request_id,
                code=-32602,
                message=f"Prompt not found: {prompt_name}",
            )

        self.register("initialize", _handle_initialize)
        self.register("ping", _handle_ping)
        self.register("tools/list", _handle_tools_list)
        self.register("tools/call", _handle_tools_call)
        self.register("resources/list", _handle_resources_list)
        self.register("resources/read", _handle_resources_read)
        self.register("prompts/list", _handle_prompts_list)
        self.register("prompts/get", _handle_prompts_get)

    async def dispatch(self, ctx: MCPRequestContext) -> dict[str, Any]:
        """Dispatch a request context through the interceptor pipeline and matching handler."""
        async def _terminal(target_ctx: MCPRequestContext) -> dict[str, Any]:
            handler = self._handlers.get(target_ctx.method)
            if handler is None:
                return self.codec.encode_error(
                    target_ctx.request_id,
                    code=JSONRPC_METHOD_NOT_FOUND,
                    message=f"Method not found: {target_ctx.method}",
                )
            try:
                return await handler(target_ctx.params, target_ctx)
            except Exception as e:
                logger.error("Unhandled error in MCP method handler", method=target_ctx.method, error=str(e))
                return self.codec.encode_error(
                    target_ctx.request_id,
                    code=JSONRPC_INTERNAL_ERROR,
                    message=f"Internal server error: {e}",
                )

        return await self.pipeline.execute(ctx, _terminal)

    async def dispatch_batch(
        self,
        requests: list[dict[str, Any]],
        *,
        event_bus: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Process a batch of JSON-RPC requests, collecting responses in matching order."""
        tasks = []
        for req in requests:
            req_id = req.get("id")
            method = str(req.get("method", ""))
            params = req.get("params") or {}
            if not isinstance(params, dict):
                params = {"value": params}

            ctx = MCPRequestContext(
                request_id=req_id,
                method=method,
                params=params,
                event_bus=event_bus,
                metadata=dict(metadata or {}),
                codec=self.codec,
            )
            tasks.append(self.dispatch(ctx))

        return await asyncio.gather(*tasks)


class AsyncStdioServerTransport:
    """Non-blocking async STDIO transport for MCP server."""

    def __init__(
        self,
        router: MCPMethodRouter,
        *,
        codec: type[MCPProtocolCodec] = MCPProtocolCodec,
        event_bus: Any | None = None,
    ) -> None:
        self.router = router
        self.codec = codec
        self.event_bus = event_bus

    async def process_line(self, line: str) -> str | None:
        """Process a single raw JSON-RPC string line and return serialized response text or None for notification."""
        line_str = line.strip()
        if not line_str:
            return None

        try:
            parsed = self.codec.parse_payload(line_str)
        except Exception as e:
            err_resp = self.codec.encode_error(None, code=JSONRPC_PARSE_ERROR, message=str(e))
            return json.dumps(err_resp)

        if isinstance(parsed, list):
            # Batch request
            batch_reqs = [{"id": r.id, "method": r.method, "params": r.params} for r in parsed]
            batch_resps = await self.router.dispatch_batch(batch_reqs, event_bus=self.event_bus)
            # Filter out responses for notifications if id was None across items, but return array
            return json.dumps(batch_resps)

        if isinstance(parsed, MCPNotification):
            ctx = MCPRequestContext(
                request_id=None,
                method=parsed.method,
                params=parsed.params,
                event_bus=self.event_bus,
                codec=self.codec,
            )
            await self.router.dispatch(ctx)
            return None

        # Standard MCPRequest
        ctx = MCPRequestContext(
            request_id=parsed.id,
            method=parsed.method,
            params=parsed.params,
            event_bus=self.event_bus,
            codec=self.codec,
        )
        resp = await self.router.dispatch(ctx)
        return json.dumps(resp)


class HarnessMCPServer:
    """STDIO-based Model Context Protocol server."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        *,
        context: Any | None = None,
        loader: Any | None = None,
        registry: MCPRegistry | None = None,
        pipeline: MCPInterceptorPipeline | None = None,
        router: MCPMethodRouter | None = None,
    ) -> None:
        self.tool_registry = tool_registry
        self.context = context
        self.loader = loader
        self.registry = registry or MCPRegistry(
            tool_registry, context=context, loader=loader
        )
        self.pipeline = pipeline or MCPInterceptorPipeline([MCPTelemetryInterceptor()])
        self.codec = MCPProtocolCodec
        self.router = router or MCPMethodRouter(
            self.registry, pipeline=self.pipeline, codec=self.codec
        )
        self.transport = AsyncStdioServerTransport(
            self.router,
            codec=self.codec,
            event_bus=getattr(context, "event_bus", None) if context else None,
        )

    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Process an incoming JSON-RPC MCP request dictionary."""
        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})
        if not isinstance(params, dict):
            params = {}

        ctx = MCPRequestContext(
            request_id=req_id,
            method=method,
            params=params,
            event_bus=getattr(self.context, "event_bus", None) if self.context else None,
            codec=self.codec,
        )
        return await self.router.dispatch(ctx)

    async def handle_batch(self, requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process a batch of incoming JSON-RPC MCP requests."""
        return await self.router.dispatch_batch(
            requests,
            event_bus=getattr(self.context, "event_bus", None) if self.context else None,
        )

    async def dispatch_raw(self, raw_text: str | bytes) -> str | None:
        """Parse raw string or bytes and dispatch through transport."""
        text = raw_text.decode("utf-8") if isinstance(raw_text, bytes) else str(raw_text)
        return await self.transport.process_line(text)

    async def run_stdio(self) -> None:
        """Run the JSON-RPC loop over standard input/output."""
        loop = sys.stdin
        for line in loop:
            line_str = line.strip()
            if not line_str:
                continue

            resp_str = await self.dispatch_raw(line_str)
            if resp_str is not None:
                sys.stdout.write(resp_str + "\n")
                sys.stdout.flush()
