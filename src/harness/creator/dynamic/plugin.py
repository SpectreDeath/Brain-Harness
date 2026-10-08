"""In-memory plugin class dynamically synthesized from Python source code or functions."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from harness.creator.dynamic.compiler import _compile_dynamic_module
from harness.creator.dynamic.inspector import ASTFunctionInspector
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.plugins.manifest import PluginManifest
from harness.plugins.tool_mount import TOOL_REGISTRY_KEY, ToolMountMixin
from harness.services.tools import ToolSpec

if TYPE_CHECKING:
    from harness.creator.scaffold import ScaffoldResult


class DynamicPythonPlugin(ToolMountMixin, HarnessPlugin):
    """An in-memory plugin dynamically synthesized from code or functions."""

    def __init__(
        self,
        name: str,
        version: str = "0.1.0",
        description: str = "",
        tools: dict[str, Callable[..., Any]] | None = None,
        provides: list[ServiceKey[Any]] | None = None,
        requires: list[ServiceKey[Any]] | None = None,
        code: str | None = None,
    ) -> None:
        self._name = name
        self._version = version
        self._description = description or f"Dynamic in-memory plugin: {name}"
        self._tools: dict[str, Callable[..., Any]] = dict(tools or {})
        self._provides = provides or []
        self._requires = requires or (ToolMountMixin.tool_mount_requires() if self._tools else [])
        self._code = code
        self._ctx: ServiceContext | None = None
        self._tool_specs: list[ToolSpec] = []

        if self._code and self._tools:
            try:
                self._tool_specs = ASTFunctionInspector.extract_tool_specs(
                    self._code,
                    self._tools,
                    provider=self._name,
                )
            except Exception:
                self._tool_specs = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def description(self) -> str:
        return self._description

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return self._provides

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return self._requires

    @property
    def trusted(self) -> bool:
        return True

    @property
    def source_code(self) -> str | None:
        return self._code

    @property
    def tools(self) -> dict[str, Callable[..., Any]]:
        return dict(self._tools)

    def infer_manifest(self, preset: str = "general") -> PluginManifest:
        """Infer a PluginManifest from the functions registered in this dynamic plugin."""
        from harness.creator.schema import SchemaInferrer

        return SchemaInferrer.infer_manifest(
            name=self.name,
            tools=self._tools,
            version=self.version,
            description=self.description,
            preset=preset,
        )

    async def reload_code(self, new_code: str) -> None:
        """Hot-reload in-memory functions from updated Python source code."""
        _, new_tools = _compile_dynamic_module(self.name, new_code)
        self._tools = new_tools
        self._code = new_code

        # If currently mounted and enabled in context, re-mount tool specs
        if self._mount_ctx and self._mount_ctx.has(TOOL_REGISTRY_KEY):
            await self.unmount_tools()
            specs = [
                ToolSpec.from_callable(func, name=tool_name, provider=self.name)
                for tool_name, func in self._tools.items()
            ]
            await self.mount_tools(specs)

    def export_project(
        self,
        target_dir: Path | str,
        *,
        author: str = "Harness Developer",
        category: str = "general",
        preset: str = "general",
        include_tests: bool = True,
        auto_validate: bool = True,
    ) -> ScaffoldResult:
        """Export this in-memory plugin to an authoritative on-disk scaffolded project."""
        from harness.creator.scaffold import PluginScaffoldEngine, ScaffoldOptions

        out_path = Path(target_dir).resolve()
        engine = PluginScaffoldEngine()
        tools_list = list(self._tools.keys()) or ["execute"]

        extra_files: dict[str, str] = {}
        if self._code:
            extra_files["main.py"] = self._code

        opts = ScaffoldOptions(
            name=self.name,
            version=self.version,
            description=self.description,
            language="python",
            tools=tools_list,
            author=author,
            category=category,
            preset=preset,
            include_tests=include_tests,
            extra_files=extra_files,
            auto_validate=auto_validate,
        )
        return engine.scaffold(out_path, options=opts)

    async def on_load(self, ctx: ServiceContext) -> None:
        self._ctx = ctx
        self.setup_tool_mount(ctx, self.name)

    async def on_enable(self) -> None:
        if not self._ctx:
            return

        if self._tool_specs:
            await self.mount_tools(self._tool_specs)
        elif self._tools:
            specs = [
                ToolSpec.from_callable(
                    func,
                    name=tool_name,
                    provider=self.name,
                )
                for tool_name, func in self._tools.items()
            ]
            await self.mount_tools(specs)

    async def on_disable(self) -> None:
        await self.unmount_tools()

    async def on_unload(self) -> None:
        self._tools = {}
        self._tool_specs = []
        self.teardown_tool_mount()
        self._ctx = None
