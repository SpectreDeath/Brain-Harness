"""General execution and typed Tool plugin archetypes."""

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


class GeneralArchetype(PluginArchetype):
    """Standard multi-tool execution archetype."""

    @property
    def name(self) -> str:
        return "general"

    @property
    def description(self) -> str:
        return "Standard execution plugin with multi-tool handler stubs"

    def generate_manifest(self, options: ScaffoldOptions) -> PluginManifest:
        entrypoint = "main.py" if options.language == "python" else ("index.ts" if options.language == "typescript" else "index.js")
        desc = options.description or f"Plugin providing capabilities for {options.name}"

        entrypoints = list(options.entrypoints) if options.entrypoints else []
        if not entrypoints:
            tools = options.tools or ["execute"]
            for t in tools:
                entrypoints.append(
                    EntrypointSpec(
                        name=t,
                        description=f"Handler for tool {t}",
                        parameters=[
                            ParameterSpec(
                                name="task",
                                type="string",
                                description=f"Task or query for {t}",
                                required=False,
                                default="",
                            )
                        ],
                        returns="dict",
                    )
                )

        provides = list(options.provides)
        if not provides and entrypoints:
            provides = [f"tool.{options.name}"]

        tags = list(options.tags)
        if "general" not in tags:
            tags.append("general")

        return PluginManifest(
            name=options.name,
            version=options.version,
            description=desc,
            language=options.language,
            entrypoint=entrypoint,
            isolation=options.isolation,
            author=options.author,
            category=options.category,
            tags=tags,
            provides=provides,
            requires=list(options.requires),
            entrypoints=entrypoints,
            dependencies=list(options.dependencies),
            metadata={"scaffolded_by": "harness.creator.archetypes", "preset": self.name},
        )

    def generate_entrypoint_code(self, options: ScaffoldOptions) -> str:
        lang = options.language.lower()
        tools = options.tools or ["execute"]

        if lang == "python":
            tool_fns = []
            for t in tools:
                tool_fns.append(
                    f'def {t}(task: str = "", **kwargs: Any) -> dict[str, Any]:\n'
                    f'    """Tool handler for {t}."""\n'
                    f'    return {{"status": "ok", "action": "{t}", "result": f"Executed {t} with {{task}}", "extra": kwargs}}\n'
                )
            tools_block = "\n".join(tool_fns)
            return (
                f'"""Main entrypoint for {options.name} plugin.\n\n'
                f'{options.description or f"Provides {options.name} capabilities."}\n'
                f'"""\n\n'
                f'from __future__ import annotations\n'
                f'from typing import Any\n\n\n'
                f'{tools_block}\n'
                f'if __name__ == "__main__":\n'
                f'    import sys, json\n'
                f'    print(json.dumps({tools[0]}("sample-task")))\n'
            )

        tool_exports = []
        for t in tools:
            param_sig = "(task = '', kwargs = {})" if lang != "typescript" else "(task: string = '', kwargs: Record<string, any> = {})"
            return_sig = "" if lang != "typescript" else ": Promise<{ status: string; action: string; result: string; extra: Record<string, any> }>"
            tool_exports.append(
                f"export async function {t}{param_sig}{return_sig} {{\n"
                f"  return {{ status: 'ok', action: '{t}', result: `Executed {t} with ${{task}}`, extra: kwargs }};\n"
                f"}}"
            )
        exports_block = "\n\n".join(tool_exports)
        return (
            f"/**\n"
            f" * Main entrypoint for {options.name} plugin.\n"
            f" */\n\n"
            f"{exports_block}\n"
        )

    def generate_test_code(self, options: ScaffoldOptions) -> str:
        lang = options.language.lower()
        tools = options.tools or ["execute"]
        first_tool = tools[0]

        if lang == "python":
            return (
                f'"""Unit tests for {options.name} plugin."""\n\n'
                f'import pytest\n'
                f'from main import {first_tool}\n\n\n'
                f'def test_{first_tool}_success():\n'
                f'    res = {first_tool}("test-run")\n'
                f'    assert res["status"] == "ok"\n'
                f'    assert res["action"] == "{first_tool}"\n'
                f'    assert "test-run" in res["result"]\n'
            )

        return (
            f'// Unit tests for {options.name}\n'
            f'import {{ {first_tool} }} from "./index.js";\n\n'
            f'test("{first_tool} returns ok", async () => {{\n'
            f'  const res = await {first_tool}("test-run");\n'
            f'  expect(res.status).toBe("ok");\n'
            f'}});\n'
        )

    def generate_project_config(self, options: ScaffoldOptions) -> tuple[str, str]:
        lang = options.language.lower()
        deps = list(options.dependencies)
        if lang == "python":
            deps_content = "\n".join(deps) if deps else "# Add requirements here\n"
            return "requirements.txt", deps_content

        pkg = {
            "name": options.name,
            "version": options.version,
            "description": options.description,
            "main": "index.ts" if lang == "typescript" else "index.js",
            "type": "module",
            "dependencies": {dep: "*" for dep in deps},
        }
        return "package.json", json.dumps(pkg, indent=2)

    def generate_extra_files(self, options: ScaffoldOptions) -> dict[str, str]:
        return {
            ".gitignore": "__pycache__/\n*.pyc\nnode_modules/\n.env\n.pytest_cache/\n",
        }


class ToolArchetype(GeneralArchetype):
    """LLM Skill / Tool archetype with structured docstrings and parameter schemas."""

    @property
    def name(self) -> str:
        return "tool"

    @property
    def description(self) -> str:
        return "Typed LLM tool and skill provider with structured schemas"

    def generate_manifest(self, options: ScaffoldOptions) -> PluginManifest:
        manifest = super().generate_manifest(options)
        manifest.category = options.category or "developer_tools"
        if "tool" not in manifest.tags:
            manifest.tags.append("tool")
        return manifest


__all__ = [
    "GeneralArchetype",
    "ToolArchetype",
]
