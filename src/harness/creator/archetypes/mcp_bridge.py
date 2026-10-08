"""Model Context Protocol (MCP) server bridge plugin archetype."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from harness.creator.archetypes.base import PluginArchetype
from harness.plugins.manifest import (
    EntrypointSpec,
    ParameterSpec,
    PluginManifest,
)

if TYPE_CHECKING:
    from harness.creator.scaffold import ScaffoldOptions


class McpBridgeArchetype(PluginArchetype):
    """Model Context Protocol (MCP) server bridge archetype."""

    @property
    def name(self) -> str:
        return "mcp_bridge"

    @property
    def description(self) -> str:
        return "Model Context Protocol bridge forwarding tool calls to external MCP servers"

    def generate_manifest(self, options: ScaffoldOptions) -> PluginManifest:
        entrypoint = "main.py" if options.language == "python" else ("index.ts" if options.language == "typescript" else "index.js")
        return PluginManifest(
            name=options.name,
            version=options.version,
            description=options.description or f"MCP Bridge plugin for {options.name}",
            language=options.language,
            entrypoint=entrypoint,
            isolation=options.isolation,
            author=options.author,
            category="bridge",
            tags=["mcp", "protocol", "bridge"],
            provides=[f"tool.{options.name}"],
            entrypoints=[
                EntrypointSpec(
                    name="mcp_call",
                    description="Forward a JSON-RPC invocation to the MCP server",
                    parameters=[
                        ParameterSpec(name="method", type="string", description="MCP tool or prompt name", required=True),
                        ParameterSpec(name="params", type="object", description="Arguments dictionary", required=False, default={}),
                    ],
                    returns="dict",
                )
            ],
            dependencies=["mcp>=1.0.0"] if options.language == "python" else ["@modelcontextprotocol/sdk"],
            metadata={"scaffolded_by": "harness.creator.archetypes", "preset": self.name},
        )

    def generate_entrypoint_code(self, options: ScaffoldOptions) -> str:
        lang = options.language.lower()
        if lang == "python":
            return (
                f'"""MCP Bridge entrypoint for {options.name}.\n"""\n\n'
                f'from __future__ import annotations\n'
                f'from typing import Any\n\n\n'
                f'def mcp_call(method: str = "tools/list", params: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:\n'
                f'    """Execute an MCP tool call over stdio transport."""\n'
                f'    return {{"status": "ok", "action": "mcp_call", "method": method, "params": params or {{}}, "extra": kwargs}}\n\n\n'
                f'if __name__ == "__main__":\n'
                f'    import json, sys\n'
                f'    print(json.dumps(mcp_call("ping")))\n'
            )

        param_sig = "(method = 'tools/list', params = {}, kwargs = {})" if lang != "typescript" else "(method: string = 'tools/list', params: Record<string, any> = {}, kwargs: Record<string, any> = {})"
        return (
            f"/**\n"
            f" * MCP Bridge entrypoint for {options.name}\n"
            f" */\n\n"
            f"export async function mcp_call{param_sig} {{\n"
            f"  return {{ status: 'ok', action: 'mcp_call', method, params, extra: kwargs }};\n"
            f"}}\n"
        )

    def generate_test_code(self, options: ScaffoldOptions) -> str:
        lang = options.language.lower()
        if lang == "python":
            return (
                f'"""Unit tests for {options.name} MCP Bridge."""\n\n'
                f'from main import mcp_call\n\n\n'
                f'def test_mcp_call():\n'
                f'    res = mcp_call("tools/list")\n'
                f'    assert res["status"] == "ok"\n'
                f'    assert res["method"] == "tools/list"\n'
            )

        return (
            f'// Unit tests for {options.name}\n'
            f'import {{ mcp_call }} from "./index.js";\n\n'
            f'test("mcp_call returns ok", async () => {{\n'
            f'  const res = await mcp_call("tools/list");\n'
            f'  expect(res.status).toBe("ok");\n'
            f'  expect(res.method).toBe("tools/list");\n'
            f'}});\n'
        )

    def generate_project_config(self, options: ScaffoldOptions) -> tuple[str, str]:
        lang = options.language.lower()
        if lang == "python":
            return "requirements.txt", "mcp>=1.0.0\n"
        pkg = {
            "name": options.name,
            "version": options.version,
            "description": options.description,
            "main": "index.ts" if lang == "typescript" else "index.js",
            "type": "module",
            "dependencies": {"@modelcontextprotocol/sdk": "^1.0.0"},
        }
        return "package.json", json.dumps(pkg, indent=2)


__all__ = [
    "McpBridgeArchetype",
]
