"""Asynchronous HTTP API wrapper plugin archetype using httpx."""

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


class ApiWrapperArchetype(PluginArchetype):
    """Asynchronous HTTP API wrapper using httpx."""

    @property
    def name(self) -> str:
        return "api_wrapper"

    @property
    def description(self) -> str:
        return "REST/HTTP API client wrapper with async connection pooling"

    def generate_manifest(self, options: ScaffoldOptions) -> PluginManifest:
        entrypoint = "main.py" if options.language == "python" else ("index.ts" if options.language == "typescript" else "index.js")
        desc = options.description or f"API wrapper plugin for {options.name}"

        tools = options.tools or ["request", "status"]
        entrypoints = []
        for t in tools:
            entrypoints.append(
                EntrypointSpec(
                    name=t,
                    description=f"Send {t} API request to upstream service",
                    parameters=[
                        ParameterSpec(name="endpoint", type="string", description="API route path", required=True),
                        ParameterSpec(name="query", type="string", description="Query string or search term", required=False, default=""),
                    ],
                    returns="dict",
                )
            )

        deps = list(options.dependencies)
        if options.language == "python" and "httpx" not in " ".join(deps):
            deps.append("httpx>=0.27.0")

        cat = options.category if options.category and options.category != "general" else "bridge"
        return PluginManifest(
            name=options.name,
            version=options.version,
            description=desc,
            language=options.language,
            entrypoint=entrypoint,
            isolation=options.isolation,
            author=options.author,
            category=cat,
            tags=["api_wrapper", "http", "network"],
            provides=[f"tool.{options.name}"],
            requires=list(options.requires),
            entrypoints=entrypoints,
            dependencies=deps,
            metadata={"scaffolded_by": "harness.creator.archetypes", "preset": self.name},
        )

    def generate_entrypoint_code(self, options: ScaffoldOptions) -> str:
        lang = options.language.lower()
        tools = options.tools or ["request", "status"]

        if lang == "python":
            tool_fns = []
            for t in tools:
                tool_fns.append(
                    f'async def {t}(endpoint: str = "", query: str = "", **kwargs: Any) -> dict[str, Any]:\n'
                    f'    """API wrapper handler for {t}."""\n'
                    f'    async with httpx.AsyncClient(timeout=30.0) as client:\n'
                    f'        # Dispatch upstream API call\n'
                    f'        return {{"status": "ok", "action": "{t}", "endpoint": endpoint, "query": query, "extra": kwargs}}\n'
                )
            tools_block = "\n".join(tool_fns)
            return (
                f'"""API Wrapper entrypoint for {options.name} plugin.\n\n'
                f'{options.description or f"Provides {options.name} API capabilities."}\n'
                f'"""\n\n'
                f'from __future__ import annotations\n'
                f'from typing import Any\n'
                f'import httpx\n\n\n'
                f'{tools_block}\n'
                f'if __name__ == "__main__":\n'
                f'    import asyncio, json\n'
                f'    print(json.dumps(asyncio.run({tools[0]}("status"))))\n'
            )

        tool_exports = []
        for t in tools:
            tool_exports.append(
                f"export async function {t}(endpoint = '', query = '', kwargs = {{}}) {{\n"
                f"  // Dispatch upstream HTTP request\n"
                f"  return {{ status: 'ok', action: '{t}', endpoint, query, extra: kwargs }};\n"
                f"}}"
            )
        exports_block = "\n\n".join(tool_exports)
        return f"/**\n * API Wrapper entrypoint for {options.name}\n */\n\n{exports_block}\n"

    def generate_test_code(self, options: ScaffoldOptions) -> str:
        lang = options.language.lower()
        tools = options.tools or ["request", "status"]
        first_tool = tools[0]

        if lang == "python":
            return (
                f'"""Unit tests for {options.name} API wrapper."""\n\n'
                f'import pytest\n'
                f'from main import {first_tool}\n\n\n'
                f'@pytest.mark.asyncio\n'
                f'async def test_{first_tool}_api_call():\n'
                f'    res = await {first_tool}("v1/status")\n'
                f'    assert res["status"] == "ok"\n'
                f'    assert res["endpoint"] == "v1/status"\n'
            )

        return (
            f'// Unit tests for {options.name}\n'
            f'import {{ {first_tool} }} from "./index.js";\n\n'
            f'test("{first_tool} returns ok", async () => {{\n'
            f'  const res = await {first_tool}("v1/status");\n'
            f'  expect(res.status).toBe("ok");\n'
            f'}});\n'
        )

    def generate_project_config(self, options: ScaffoldOptions) -> tuple[str, str]:
        lang = options.language.lower()
        deps = list(options.dependencies)
        if lang == "python":
            if "httpx" not in " ".join(deps):
                deps.append("httpx>=0.27.0")
            return "requirements.txt", "\n".join(deps)

        pkg = {
            "name": options.name,
            "version": options.version,
            "description": options.description,
            "main": "index.ts" if lang == "typescript" else "index.js",
            "type": "module",
            "dependencies": {dep: "*" for dep in deps} if deps else {"axios": "^1.7.0"},
        }
        return "package.json", json.dumps(pkg, indent=2)


__all__ = [
    "ApiWrapperArchetype",
]
