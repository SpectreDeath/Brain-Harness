"""MCP (Model Context Protocol) STDIO server for Harness.

Exposes all registered Harness tools and execution surfaces to any MCP client
(such as Claude Desktop, VS Code, Cursor, or external orchestrators) via STDIO.
"""

from __future__ import annotations

import inspect
import json
import sys
from typing import Any

import structlog

from harness.mcp.protocol import (
    JSONRPC_METHOD_NOT_FOUND,
    JSONRPC_PARSE_ERROR,
    MCPPrompt,
    MCPProtocolCodec,
    MCPResource,
)
from harness.services.tools import ToolRegistry

logger = structlog.get_logger()



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

    def register_prompt(self, prompt: MCPPrompt) -> None:
        """Register a custom MCP prompt template."""
        self._custom_prompts[prompt.name] = prompt

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


class HarnessMCPServer:
    """STDIO-based Model Context Protocol server."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        *,
        context: Any | None = None,
        loader: Any | None = None,
        registry: MCPRegistry | None = None,
    ) -> None:
        self.tool_registry = tool_registry
        self.context = context
        self.loader = loader
        self.registry = registry or MCPRegistry(
            tool_registry, context=context, loader=loader
        )
        self.codec = MCPProtocolCodec

    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Process an incoming JSON-RPC MCP request dictionary."""
        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})
        if not isinstance(params, dict):
            params = {}

        if method == "initialize":
            return self.codec.build_initialize_response(
                req_id,
                server_name="harness-mcp",
                version="0.1.0",
            )

        if method == "tools/list":
            tools_list = self.tool_registry.to_mcp_tools(enabled_only=False)
            return self.codec.build_tools_list_response(req_id, tools_list)

        if method == "tools/call":
            tool_name = str(params.get("name", ""))
            arguments = params.get("arguments", {})
            if not isinstance(arguments, dict):
                arguments = {}

            result = await self.tool_registry.invoke(tool_name, arguments)
            is_error = result.get("status") == "error"
            content_payload = result.get("result", result.get("error", "done"))

            return self.codec.build_tool_call_response(
                req_id,
                result=content_payload,
                is_error=is_error,
            )

        if method == "resources/list":
            resources = self.registry.list_resources()
            return self.codec.build_resources_list_response(req_id, resources)

        if method == "resources/read":
            uri = str(params.get("uri", ""))
            res_result = await self.registry.read_resource(uri)
            if res_result is not None:
                content, mime = res_result
                return self.codec.build_resource_read_response(
                    req_id, uri, content, mime_type=mime
                )

            return self.codec.encode_error(
                req_id,
                code=-32602,
                message=f"Resource not found: {uri}",
            )

        if method == "prompts/list":
            prompts = self.registry.list_prompts()
            return self.codec.build_prompts_list_response(req_id, prompts)

        if method == "prompts/get":
            prompt_name = str(params.get("name", ""))
            arguments = params.get("arguments", {})
            prompt_result = await self.registry.get_prompt(prompt_name, arguments)
            if prompt_result is not None:
                desc, messages = prompt_result
                return self.codec.build_prompt_get_response(
                    req_id,
                    description=desc,
                    messages=messages,
                )

            return self.codec.encode_error(
                req_id,
                code=-32602,
                message=f"Prompt not found: {prompt_name}",
            )

        return self.codec.encode_error(
            req_id,
            code=JSONRPC_METHOD_NOT_FOUND,
            message=f"Method not found: {method}",
        )

    async def run_stdio(self) -> None:
        """Run the JSON-RPC loop over standard input/output."""
        loop = sys.stdin
        for line in loop:
            line_str = line.strip()
            if not line_str:
                continue

            try:
                mcp_req = self.codec.parse_request(line_str)
                resp = await self.handle_request({
                    "id": mcp_req.id,
                    "method": mcp_req.method,
                    "params": mcp_req.params,
                })
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
            except Exception as e:
                err_resp = self.codec.encode_error(
                    None,
                    code=JSONRPC_PARSE_ERROR,
                    message=str(e),
                )
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()

