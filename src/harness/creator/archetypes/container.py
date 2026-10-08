"""Containerized plugin archetype with Dockerfile and sandbox container isolation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from harness.creator.archetypes.base import PluginArchetype
from harness.plugins.manifest import (
    EntrypointSpec,
    IsolationMode,
    ParameterSpec,
    PluginManifest,
)

if TYPE_CHECKING:
    from harness.creator.scaffold import ScaffoldOptions


class ContainerArchetype(PluginArchetype):
    """Containerized plugin with Dockerfile and sandbox container specs."""

    @property
    def name(self) -> str:
        return "container"

    @property
    def description(self) -> str:
        return "Containerized plugin with Dockerfile and sandbox container isolation"

    def generate_manifest(self, options: ScaffoldOptions) -> PluginManifest:
        entrypoint = "main.py" if options.language == "python" else ("index.ts" if options.language == "typescript" else "index.js")
        desc = options.description or f"Containerized plugin for {options.name}"

        tools = options.tools or ["execute"]
        entrypoints = [
            EntrypointSpec(
                name=t,
                description=f"Containerized execution handler for {t}",
                parameters=[
                    ParameterSpec(name="command", type="string", description="Command or task payload", required=False, default=""),
                ],
                returns="dict",
            )
            for t in tools
        ]

        return PluginManifest(
            name=options.name,
            version=options.version,
            description=desc,
            language=options.language,
            entrypoint=entrypoint,
            isolation=IsolationMode.DOCKER,
            author=options.author,
            category=options.category or "system",
            tags=["container", "docker", "sandboxed"],
            provides=[f"container.{options.name}"],
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
                    f'def {t}(command: str = "", **kwargs: Any) -> dict[str, Any]:\n'
                    f'    """Execute inside container environment."""\n'
                    f'    return {{"status": "ok", "action": "{t}", "command": command, "container": True, "extra": kwargs}}\n'
                )
            tools_block = "\n".join(tool_fns)
            return (
                f'"""Containerized entrypoint for {options.name}.\n"""\n\n'
                f'from __future__ import annotations\n'
                f'from typing import Any\n\n\n'
                f'{tools_block}\n'
                f'if __name__ == "__main__":\n'
                f'    import json\n'
                f'    print(json.dumps({tools[0]}("healthcheck")))\n'
            )

        tool_exports = []
        for t in tools:
            param_sig = "(command = '', kwargs = {})" if lang != "typescript" else "(command: string = '', kwargs: Record<string, any> = {})"
            tool_exports.append(
                f"export async function {t}{param_sig} {{\n"
                f"  return {{ status: 'ok', action: '{t}', command, container: true, extra: kwargs }};\n"
                f"}}"
            )
        exports_block = "\n\n".join(tool_exports)
        return (
            f"/**\n"
            f" * Containerized entrypoint for {options.name}\n"
            f" */\n\n"
            f"{exports_block}\n"
        )

    def generate_test_code(self, options: ScaffoldOptions) -> str:
        lang = options.language.lower()
        tools = options.tools or ["execute"]
        first_tool = tools[0]
        if lang == "python":
            return (
                f'"""Unit tests for containerized {options.name}."""\n\n'
                f'from main import {first_tool}\n\n\n'
                f'def test_{first_tool}_container():\n'
                f'    res = {first_tool}("test-command")\n'
                f'    assert res["status"] == "ok"\n'
                f'    assert res["container"] is True\n'
            )

        return (
            f'// Unit tests for {options.name}\n'
            f'import {{ {first_tool} }} from "./index.js";\n\n'
            f'test("{first_tool} container execution", async () => {{\n'
            f'  const res = await {first_tool}("test-command");\n'
            f'  expect(res.status).toBe("ok");\n'
            f'  expect(res.container).toBe(true);\n'
            f'}});\n'
        )

    def generate_project_config(self, options: ScaffoldOptions) -> tuple[str, str]:
        lang = options.language.lower()
        if lang == "python":
            return "requirements.txt", "# Container dependencies\n"
        pkg = {
            "name": options.name,
            "version": options.version,
            "description": options.description,
            "main": "index.ts" if lang == "typescript" else "index.js",
            "type": "module",
            "dependencies": {dep: "*" for dep in options.dependencies},
        }
        return "package.json", json.dumps(pkg, indent=2)

    def generate_extra_files(self, options: ScaffoldOptions) -> dict[str, str]:
        lang = options.language.lower()
        if lang == "python":
            dockerfile = (
                "FROM python:3.11-slim\n\n"
                "WORKDIR /app\n\n"
                "COPY requirements.txt .\n"
                "RUN pip install --no-cache-dir -r requirements.txt\n\n"
                "COPY . .\n\n"
                'ENTRYPOINT ["python", "main.py"]\n'
            )
        elif lang == "typescript":
            dockerfile = (
                "FROM node:20-alpine\n\n"
                "WORKDIR /app\n\n"
                "COPY package*.json tsconfig.json ./\n"
                "RUN npm install\n\n"
                "COPY . .\n\n"
                'ENTRYPOINT ["npx", "tsx", "index.ts"]\n'
            )
        else:
            dockerfile = (
                "FROM node:20-alpine\n\n"
                "WORKDIR /app\n\n"
                "COPY package*.json ./\n"
                "RUN npm install\n\n"
                "COPY . .\n\n"
                'ENTRYPOINT ["node", "index.js"]\n'
            )
        dockerignore = ".git\n__pycache__\n*.pyc\n.pytest_cache\nnode_modules\n"
        return {
            "Dockerfile": dockerfile,
            ".dockerignore": dockerignore,
        }


__all__ = [
    "ContainerArchetype",
]
