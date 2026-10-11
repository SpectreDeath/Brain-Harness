"""Method router and JSON-RPC dispatching for Model Context Protocol."""

from __future__ import annotations

import asyncio
import sys
from typing import Any

import structlog

from harness.mcp.protocol import (
    JSONRPC_INTERNAL_ERROR,
    JSONRPC_METHOD_NOT_FOUND,
    MCPProtocolCodec,
)
from harness.mcp.server.context import MCPHandler, MCPRequestContext
from harness.mcp.server.interceptors import MCPInterceptorPipeline
from harness.mcp.server.registry import MCPRegistry

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

logger = structlog.get_logger()


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


__all__ = [
    "MCPMethodRouter",
]
