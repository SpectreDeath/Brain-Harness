"""Core ServiceProvider plugin archetype registering typed ServiceKey contracts."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from harness.creator.archetypes.base import PluginArchetype
from harness.plugins.manifest import (
    EntrypointSpec,
    IsolationMode,
    PluginManifest,
)

if TYPE_CHECKING:
    from harness.creator.scaffold import ScaffoldOptions


class ServiceArchetype(PluginArchetype):
    """Direct in-process or lifecycle-managed ServiceKey provider."""

    @property
    def name(self) -> str:
        return "service"

    @property
    def description(self) -> str:
        return "Core ServiceProvider plugin registering typed ServiceKey contracts"

    def generate_manifest(self, options: ScaffoldOptions) -> PluginManifest:
        entrypoint = "main.py" if options.language == "python" else ("index.ts" if options.language == "typescript" else "index.js")
        service_key_name = f"service.{options.name}"
        cat = options.category if options.category and options.category != "general" else "core"
        return PluginManifest(
            name=options.name,
            version=options.version,
            description=options.description or f"Service provider for {options.name}",
            language=options.language,
            entrypoint=entrypoint,
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

    def generate_entrypoint_code(self, options: ScaffoldOptions) -> str:
        lang = options.language.lower()
        if lang == "python":
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
                f'def get_status(**kwargs: Any) -> dict[str, Any]:\n'
                f'    """Query service health status."""\n'
                f'    return {{"status": "healthy", "service": "{options.name}", "extra": kwargs}}\n\n\n'
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

        param_sig = "(kwargs = {})" if lang != "typescript" else "(kwargs: Record<string, any> = {})"
        return_sig = "" if lang != "typescript" else ": Promise<{ status: string; service: string; extra: Record<string, any> }>"
        return (
            f"/**\n"
            f" * Service provider for {options.name}\n"
            f" */\n\n"
            f"export async function get_status{param_sig}{return_sig} {{\n"
            f"  return {{ status: 'healthy', service: '{options.name}', extra: kwargs }};\n"
            f"}}\n"
        )

    def generate_test_code(self, options: ScaffoldOptions) -> str:
        lang = options.language.lower()
        if lang == "python":
            service_class = "".join(part.capitalize() for part in options.name.replace("-", "_").split("_")) + "Service"
            plugin_class = service_class + "Plugin"

            return (
                f'"""Unit tests for {plugin_class}."""\n\n'
                f'import pytest\n'
                f'from harness.kernel.context import ServiceContext, ServiceKey\n'
                f'from main import {plugin_class}, {service_class}, SERVICE_KEY, get_status\n\n\n'
                f'@pytest.mark.asyncio\n'
                f'async def test_service_registration():\n'
                f'    ctx = ServiceContext()\n'
                f'    plugin = {plugin_class}()\n'
                f'    await plugin.on_load(ctx)\n'
                f'    service = ctx.require(SERVICE_KEY)\n'
                f'    assert service.get_status()["status"] == "healthy"\n'
                f'    assert get_status()["status"] == "healthy"\n'
            )

        return (
            f'// Unit tests for {options.name}\n'
            f'import {{ get_status }} from "./index.js";\n\n'
            f'test("get_status returns healthy", async () => {{\n'
            f'  const res = await get_status();\n'
            f'  expect(res.status).toBe("healthy");\n'
            f'}});\n'
        )

    def generate_project_config(self, options: ScaffoldOptions) -> tuple[str, str]:
        lang = options.language.lower()
        if lang == "python":
            return "requirements.txt", "# In-process Harness core dependency\n"
        pkg = {
            "name": options.name,
            "version": options.version,
            "description": options.description or f"Service provider {options.name}",
            "main": "index.ts" if lang == "typescript" else "index.js",
            "type": "module",
            "dependencies": {dep: "*" for dep in options.dependencies},
        }
        return "package.json", json.dumps(pkg, indent=2)


__all__ = [
    "ServiceArchetype",
]
