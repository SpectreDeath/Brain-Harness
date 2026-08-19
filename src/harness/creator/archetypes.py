"""Plugin Archetypes — polymorphic template and code generation strategies.

Provides deep, self-contained archetypes for diverse plugin topologies:
    - GeneralArchetype: Standard multi-tool execution boilerplate
    - ToolArchetype: LLM skill / tool provider with typed signatures
    - ApiWrapperArchetype: Async HTTP client wrapper using httpx
    - ServiceArchetype: Full HarnessPlugin subclass registering custom ServiceKeys
    - McpBridgeArchetype: Model Context Protocol (MCP) server bridge client
    - AgenticWorkflowArchetype: Autonomous agent workflow loop with multi-step planning
    - ContainerArchetype: Containerized plugin with Dockerfile and sandbox container isolation
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from harness.plugins.manifest import (
    EntrypointSpec,
    IsolationMode,
    ParameterSpec,
    PluginManifest,
)


class PluginArchetype(ABC):
    """Abstract strategy for generating plugin manifests, source code, and tests."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique archetype preset identifier (e.g., 'general', 'tool', 'api_wrapper')."""

    @property
    def description(self) -> str:
        """Human-readable archetype description."""
        return f"Archetype preset for {self.name}"

    @abstractmethod
    def generate_manifest(self, options: Any) -> PluginManifest:
        """Generate a validated PluginManifest."""

    @abstractmethod
    def generate_entrypoint_code(self, options: Any) -> str:
        """Generate entrypoint source code."""

    @abstractmethod
    def generate_test_code(self, options: Any) -> str:
        """Generate unit test code."""

    @abstractmethod
    def generate_project_config(self, options: Any) -> tuple[str, str]:
        """Generate package/requirements configuration (filename, content)."""

    def generate_extra_files(self, options: Any) -> dict[str, str]:
        """Generate optional auxiliary files (relative_path -> file_content)."""
        return {}


class GeneralArchetype(PluginArchetype):
    """Standard multi-tool execution archetype."""

    @property
    def name(self) -> str:
        return "general"

    @property
    def description(self) -> str:
        return "Standard execution plugin with multi-tool handler stubs"

    def generate_manifest(self, options: Any) -> PluginManifest:
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

    def generate_entrypoint_code(self, options: Any) -> str:
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

    def generate_test_code(self, options: Any) -> str:
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

    def generate_project_config(self, options: Any) -> tuple[str, str]:
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

    def generate_extra_files(self, options: Any) -> dict[str, str]:
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

    def generate_manifest(self, options: Any) -> PluginManifest:
        manifest = super().generate_manifest(options)
        manifest.category = options.category or "developer_tools"
        if "tool" not in manifest.tags:
            manifest.tags.append("tool")
        return manifest


class ApiWrapperArchetype(PluginArchetype):
    """Asynchronous HTTP API wrapper using httpx."""

    @property
    def name(self) -> str:
        return "api_wrapper"

    @property
    def description(self) -> str:
        return "REST/HTTP API client wrapper with async connection pooling"

    def generate_manifest(self, options: Any) -> PluginManifest:
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

    def generate_entrypoint_code(self, options: Any) -> str:
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

    def generate_test_code(self, options: Any) -> str:
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

    def generate_project_config(self, options: Any) -> tuple[str, str]:
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


class ServiceArchetype(PluginArchetype):
    """Direct in-process or lifecycle-managed ServiceKey provider."""

    @property
    def name(self) -> str:
        return "service"

    @property
    def description(self) -> str:
        return "Core ServiceProvider plugin registering typed ServiceKey contracts"

    def generate_manifest(self, options: Any) -> PluginManifest:
        service_key_name = f"service.{options.name}"
        cat = options.category if options.category and options.category != "general" else "core"
        return PluginManifest(
            name=options.name,
            version=options.version,
            description=options.description or f"Service provider for {options.name}",
            language=options.language,
            entrypoint="main.py",
            isolation=IsolationMode.IN_PROCESS,
            trusted=True,
            author=options.author,
            category=cat,
            tags=["service", "core_provider"],
            provides=[service_key_name],
            requires=list(options.requires),
            entrypoints=[EntrypointSpec(name="get_status", description="Query service health status")],
            dependencies=list(options.dependencies),
            metadata={"scaffolded_by": "harness.creator.archetypes", "preset": self.name},
        )

    def generate_entrypoint_code(self, options: Any) -> str:
        service_class = "".join(part.capitalize() for part in options.name.replace("-", "_").split("_")) + "Service"
        plugin_class = service_class + "Plugin"
        service_key_name = f"service.{options.name}"

        return (
            f'"""Service provider implementation for {options.name}.\n"""\n\n'
            f'from __future__ import annotations\n'
            f'from typing import Any\n'
            f'from harness.kernel.context import ServiceContext, ServiceKey\n'
            f'from harness.plugins.base import HarnessPlugin\n\n\n'
            f'SERVICE_KEY: ServiceKey[{service_class}] = ServiceKey("{service_key_name}")\n\n\n'
            f'class {service_class}:\n'
            f'    """Service instance for {options.name}."""\n\n'
            f'    def __init__(self) -> None:\n'
            f'        self.initialized = True\n\n'
            f'    def get_status(self) -> dict[str, Any]:\n'
            f'        return {{"status": "healthy", "service": "{options.name}"}}\n\n\n'
            f'class {plugin_class}(HarnessPlugin):\n'
            f'    """Plugin wrapper providing {service_key_name}."""\n\n'
            f'    def __init__(self) -> None:\n'
            f'        self._service = {service_class}()\n'
            f'        self._ctx: ServiceContext | None = None\n\n'
            f'    @property\n'
            f'    def name(self) -> str:\n'
            f'        return "{options.name}"\n\n'
            f'    @property\n'
            f'    def provides(self) -> list[ServiceKey[Any]]:\n'
            f'        return [SERVICE_KEY]\n\n'
            f'    @property\n'
            f'    def trusted(self) -> bool:\n'
            f'        return True\n\n'
            f'    async def on_load(self, ctx: ServiceContext) -> None:\n'
            f'        self._ctx = ctx\n'
            f'        ctx.provide(SERVICE_KEY, self._service, provider=self.name)\n\n'
            f'    async def on_unload(self) -> None:\n'
            f'        self._ctx = None\n'
        )

    def generate_test_code(self, options: Any) -> str:
        service_class = "".join(part.capitalize() for part in options.name.replace("-", "_").split("_")) + "Service"
        plugin_class = service_class + "Plugin"
        service_key_name = f"service.{options.name}"

        return (
            f'"""Unit tests for {plugin_class}."""\n\n'
            f'import pytest\n'
            f'from harness.kernel.context import ServiceContext, ServiceKey\n'
            f'from main import {plugin_class}, {service_class}, SERVICE_KEY\n\n\n'
            f'@pytest.mark.asyncio\n'
            f'async def test_service_registration():\n'
            f'    ctx = ServiceContext()\n'
            f'    plugin = {plugin_class}()\n'
            f'    await plugin.on_load(ctx)\n'
            f'    service = ctx.require(SERVICE_KEY)\n'
            f'    assert service.get_status()["status"] == "healthy"\n'
        )

    def generate_project_config(self, options: Any) -> tuple[str, str]:
        return "requirements.txt", "# In-process Harness core dependency\n"


class McpBridgeArchetype(PluginArchetype):
    """Model Context Protocol (MCP) server bridge archetype."""

    @property
    def name(self) -> str:
        return "mcp_bridge"

    @property
    def description(self) -> str:
        return "Model Context Protocol bridge forwarding tool calls to external MCP servers"

    def generate_manifest(self, options: Any) -> PluginManifest:
        return PluginManifest(
            name=options.name,
            version=options.version,
            description=options.description or f"MCP Bridge plugin for {options.name}",
            language=options.language,
            entrypoint="main.py",
            isolation=IsolationMode.SUBPROCESS,
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
            dependencies=["mcp>=1.0.0"],
            metadata={"scaffolded_by": "harness.creator.archetypes", "preset": self.name},
        )

    def generate_entrypoint_code(self, options: Any) -> str:
        return (
            f'"""MCP Bridge entrypoint for {options.name}.\n"""\n\n'
            f'from __future__ import annotations\n'
            f'from typing import Any\n\n\n'
            f'def mcp_call(method: str, params: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:\n'
            f'    """Execute an MCP tool call over stdio transport."""\n'
            f'    return {{"status": "ok", "action": "mcp_call", "method": method, "params": params or {{}}, "extra": kwargs}}\n\n\n'
            f'if __name__ == "__main__":\n'
            f'    import json, sys\n'
            f'    print(json.dumps(mcp_call("ping")))\n'
        )

    def generate_test_code(self, options: Any) -> str:
        return (
            f'"""Unit tests for {options.name} MCP Bridge."""\n\n'
            f'from main import mcp_call\n\n\n'
            f'def test_mcp_call():\n'
            f'    res = mcp_call("tools/list")\n'
            f'    assert res["status"] == "ok"\n'
            f'    assert res["method"] == "tools/list"\n'
        )

    def generate_project_config(self, options: Any) -> tuple[str, str]:
        return "requirements.txt", "mcp>=1.0.0\n"


class AgenticWorkflowArchetype(PluginArchetype):
    """Autonomous agent workflow with multi-step plan, act, and evaluate loops."""

    @property
    def name(self) -> str:
        return "agentic_workflow"

    @property
    def description(self) -> str:
        return "Autonomous agent workflow loop with multi-step planning and evaluation hooks"

    def generate_manifest(self, options: Any) -> PluginManifest:
        entrypoint = "main.py" if options.language == "python" else ("index.ts" if options.language == "typescript" else "index.js")
        desc = options.description or f"Agentic workflow engine for {options.name}"

        tools = options.tools or ["plan", "execute_step", "evaluate"]
        entrypoints = [
            EntrypointSpec(
                name="plan",
                description="Formulate an execution plan for a goal",
                parameters=[
                    ParameterSpec(name="goal", type="string", description="High-level goal or task", required=True),
                ],
                returns="dict",
            ),
            EntrypointSpec(
                name="execute_step",
                description="Execute an individual planned action step",
                parameters=[
                    ParameterSpec(name="step", type="string", description="Step action to execute", required=True),
                    ParameterSpec(name="context", type="object", description="Context data", required=False, default={}),
                ],
                returns="dict",
            ),
            EntrypointSpec(
                name="evaluate",
                description="Evaluate outcome against expected termination criteria",
                parameters=[
                    ParameterSpec(name="result", type="object", description="Execution result payload", required=True),
                ],
                returns="dict",
            ),
        ]

        cat = options.category if options.category and options.category != "general" else "agent"
        return PluginManifest(
            name=options.name,
            version=options.version,
            description=desc,
            language=options.language,
            entrypoint=entrypoint,
            isolation=options.isolation,
            author=options.author,
            category=cat,
            tags=["agent", "workflow", "autonomous", "planning"],
            provides=[f"workflow.{options.name}"],
            requires=list(options.requires),
            entrypoints=entrypoints,
            dependencies=list(options.dependencies),
            metadata={"scaffolded_by": "harness.creator.archetypes", "preset": self.name},
        )

    def generate_entrypoint_code(self, options: Any) -> str:
        return (
            f'"""Agentic Workflow engine for {options.name}.\n\n'
            f'{options.description or f"Implements autonomous agent workflow logic for {options.name}."}\n'
            f'"""\n\n'
            f'from __future__ import annotations\n'
            f'from typing import Any\n\n\n'
            f'def plan(goal: str, **kwargs: Any) -> dict[str, Any]:\n'
            f'    """Formulate multi-step action plan for goal."""\n'
            f'    steps = [\n'
            f'        f"1. Analyze requirements for: {{goal}}",\n'
            f'        f"2. Execute core operations",\n'
            f'        f"3. Verify and synthesize results",\n'
            f'    ]\n'
            f'    return {{"status": "ok", "action": "plan", "goal": goal, "steps": steps, "extra": kwargs}}\n\n\n'
            f'def execute_step(step: str, context: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:\n'
            f'    """Execute an individual step action."""\n'
            f'    ctx = context or {{}}\n'
            f'    return {{"status": "ok", "action": "execute_step", "step": step, "output": f"Completed: {{step}}", "context": ctx}}\n\n\n'
            f'def evaluate(result: dict[str, Any], **kwargs: Any) -> dict[str, Any]:\n'
            f'    """Evaluate results against completion criteria."""\n'
            f'    is_success = result.get("status") == "ok"\n'
            f'    return {{"status": "ok", "action": "evaluate", "passed": is_success, "score": 1.0 if is_success else 0.0}}\n\n\n'
            f'if __name__ == "__main__":\n'
            f'    import json\n'
            f'    p = plan("Sample Agent Task")\n'
            f'    print(json.dumps(p, indent=2))\n'
        )

    def generate_test_code(self, options: Any) -> str:
        return (
            f'"""Unit tests for {options.name} agentic workflow."""\n\n'
            f'from main import plan, execute_step, evaluate\n\n\n'
            f'def test_workflow_lifecycle():\n'
            f'    plan_res = plan("Test Goal")\n'
            f'    assert plan_res["status"] == "ok"\n'
            f'    assert len(plan_res["steps"]) == 3\n\n'
            f'    step_res = execute_step(plan_res["steps"][0])\n'
            f'    assert step_res["status"] == "ok"\n'
            f'    assert "Completed:" in step_res["output"]\n\n'
            f'    eval_res = evaluate(step_res)\n'
            f'    assert eval_res["status"] == "ok"\n'
            f'    assert eval_res["passed"] is True\n'
        )

    def generate_project_config(self, options: Any) -> tuple[str, str]:
        return "requirements.txt", "# Agent workflow dependencies\n"

    def generate_extra_files(self, options: Any) -> dict[str, str]:
        readme = (
            f"# {options.name}\n\n"
            f"{options.description or 'Autonomous Agent Workflow Plugin'}\n\n"
            f"## Workflow Stages\n"
            f"- `plan(goal)`: Generates actionable steps\n"
            f"- `execute_step(step, context)`: Dispatches step execution\n"
            f"- `evaluate(result)`: Analyzes step outputs and completion\n"
        )
        return {
            "README.md": readme,
            ".gitignore": "__pycache__/\n*.pyc\n.pytest_cache/\n",
        }


class ContainerArchetype(PluginArchetype):
    """Containerized plugin with Dockerfile and sandbox container specs."""

    @property
    def name(self) -> str:
        return "container"

    @property
    def description(self) -> str:
        return "Containerized plugin with Dockerfile and sandbox container isolation"

    def generate_manifest(self, options: Any) -> PluginManifest:
        entrypoint = "main.py" if options.language == "python" else "index.js"
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

    def generate_entrypoint_code(self, options: Any) -> str:
        tools = options.tools or ["execute"]
        first_tool = tools[0]
        return (
            f'"""Containerized entrypoint for {options.name}.\n"""\n\n'
            f'from __future__ import annotations\n'
            f'from typing import Any\n\n\n'
            f'def {first_tool}(command: str = "", **kwargs: Any) -> dict[str, Any]:\n'
            f'    """Execute inside container environment."""\n'
            f'    return {{"status": "ok", "action": "{first_tool}", "command": command, "container": True, "extra": kwargs}}\n\n\n'
            f'if __name__ == "__main__":\n'
            f'    import json\n'
            f'    print(json.dumps({first_tool}("healthcheck")))\n'
        )

    def generate_test_code(self, options: Any) -> str:
        tools = options.tools or ["execute"]
        first_tool = tools[0]
        return (
            f'"""Unit tests for containerized {options.name}."""\n\n'
            f'from main import {first_tool}\n\n\n'
            f'def test_{first_tool}_container():\n'
            f'    res = {first_tool}("test-command")\n'
            f'    assert res["status"] == "ok"\n'
            f'    assert res["container"] is True\n'
        )

    def generate_project_config(self, options: Any) -> tuple[str, str]:
        return "requirements.txt", "# Container dependencies\n"

    def generate_extra_files(self, options: Any) -> dict[str, str]:
        dockerfile = (
            "FROM python:3.11-slim\n\n"
            "WORKDIR /app\n\n"
            "COPY requirements.txt .\n"
            "RUN pip install --no-cache-dir -r requirements.txt\n\n"
            "COPY . .\n\n"
            'ENTRYPOINT ["python", "main.py"]\n'
        )
        dockerignore = ".git\n__pycache__\n*.pyc\n.pytest_cache\n"
        return {
            "Dockerfile": dockerfile,
            ".dockerignore": dockerignore,
        }


class ArchetypeRegistry:
    """Authoritative registry for plugin scaffolding archetypes."""

    _archetypes: dict[str, PluginArchetype] = {}
    _aliases: dict[str, str] = {
        "workflow": "agentic_workflow",
        "agent": "agentic_workflow",
        "agentic": "agentic_workflow",
        "docker": "container",
        "containerized": "container",
        "api": "api_wrapper",
    }

    @classmethod
    def register(cls, archetype: PluginArchetype | type[PluginArchetype]) -> None:
        """Register a new plugin archetype strategy."""
        instance = archetype() if isinstance(archetype, type) else archetype
        cls._archetypes[instance.name.lower()] = instance

    @classmethod
    def unregister(cls, name: str) -> bool:
        """Unregister an archetype preset by name. Returns True if removed."""
        clean_name = (name or "").lower().replace("-", "_")
        resolved = cls._aliases.get(clean_name, clean_name)
        if resolved in cls._archetypes:
            del cls._archetypes[resolved]
            return True
        return False

    @classmethod
    def has(cls, name: str) -> bool:
        """Check if an archetype preset is registered."""
        clean_name = (name or "").lower().replace("-", "_")
        resolved = cls._aliases.get(clean_name, clean_name)
        return resolved in cls._archetypes

    @classmethod
    def get(cls, name: str) -> PluginArchetype:
        """Retrieve an archetype by preset name, falling back to GeneralArchetype."""
        clean_name = (name or "general").lower().replace("-", "_")
        resolved = cls._aliases.get(clean_name, clean_name)
        return cls._archetypes.get(resolved, cls._archetypes.get("general", GeneralArchetype()))

    @classmethod
    def list_archetypes(cls) -> list[dict[str, str]]:
        """List all registered archetypes and their descriptions."""
        return [
            {"name": arch.name, "description": arch.description}
            for arch in cls._archetypes.values()
        ]

    @classmethod
    def reset(cls) -> None:
        """Reset the registry to built-in default archetypes."""
        cls._archetypes.clear()
        cls.register(GeneralArchetype())
        cls.register(ToolArchetype())
        cls.register(ApiWrapperArchetype())
        cls.register(ServiceArchetype())
        cls.register(McpBridgeArchetype())
        cls.register(AgenticWorkflowArchetype())
        cls.register(ContainerArchetype())


# Register built-in default archetypes
ArchetypeRegistry.reset()

__all__ = [
    "AgenticWorkflowArchetype",
    "ApiWrapperArchetype",
    "ArchetypeRegistry",
    "ContainerArchetype",
    "GeneralArchetype",
    "McpBridgeArchetype",
    "PluginArchetype",
    "ServiceArchetype",
    "ToolArchetype",
]
