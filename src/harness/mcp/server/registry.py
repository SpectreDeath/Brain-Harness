"""Authoritative registry for MCP tools, resources, and prompt templates."""

from __future__ import annotations

import inspect
import sys
from typing import Any

from harness.mcp.protocol import MCPPrompt, MCPResource
from harness.services.tools import ToolRegistry

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


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


__all__ = [
    "MCPRegistry",
]
