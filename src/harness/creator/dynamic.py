"""Creator mode — in-memory plugin building, hot-reloading, and project export.

Inspired by DeepSeek Harness's Creator Mode presets, this allows:
    1. In-memory plugin construction from raw Python code or functions
    2. Automatic AST parameter extraction and manifest inference
    3. Live hot-reloading of dynamic in-memory tools
    4. 1-line bidirectional export to scaffolded on-disk projects
    5. Interactive scaffolding of new plugins
    6. Live runtime introspection of the service dependency graph
"""

from __future__ import annotations

import ast
import inspect
import types
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from harness.creator.introspection import RuntimeIntrospector
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.plugins.manifest import (
    EntrypointSpec,
    IsolationMode,
    ParameterSpec,
    PluginManifest,
)
from harness.plugins.tool_mount import TOOL_REGISTRY_KEY, ToolMountMixin
from harness.services.tools import ToolSpec

if TYPE_CHECKING:
    from harness.creator.scaffold import ScaffoldResult

logger = structlog.get_logger()


def _compile_dynamic_module(
    name: str,
    code: str,
) -> tuple[types.ModuleType, dict[str, Callable[..., Any]]]:
    """Compile and extract callables from raw Python source code.

    Authoritative single execution site for dynamic in-memory plugins.
    """
    # Pre-validate syntax before executing
    try:
        ast.parse(code, filename=f"<dynamic_plugin_{name}>")
    except SyntaxError as e:
        raise ValueError(
            f"Syntax error in dynamic plugin '{name}': {e.msg} (line {e.lineno})"
        ) from e

    module = types.ModuleType(f"dynamic_plugin_{name}")
    try:
        exec(code, module.__dict__)  # noqa: S102
    except Exception as e:
        raise RuntimeError(
            f"Execution error in dynamic plugin '{name}': {e}"
        ) from e

    tools: dict[str, Callable[..., Any]] = {}
    for attr_name in dir(module):
        if not attr_name.startswith("_"):
            attr = getattr(module, attr_name)
            if callable(attr):
                tools[attr_name] = attr

    logger.info("Compiled dynamic in-memory module", name=name, tools_count=len(tools))
    return module, tools


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

        if self._tools:
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
        self.teardown_tool_mount()
        self._ctx = None


class DynamicPluginBuilder:
    """Factory for building in-memory or on-disk plugins dynamically."""

    @staticmethod
    def from_functions(
        name: str,
        functions: list[Callable[..., Any]],
        version: str = "0.1.0",
        description: str = "",
    ) -> DynamicPythonPlugin:
        """Create a live in-memory plugin from a list of Python callables."""
        tools_dict = {fn.__name__: fn for fn in functions}
        return DynamicPythonPlugin(
            name=name,
            version=version,
            description=description,
            tools=tools_dict,
        )

    @staticmethod
    def from_code(
        name: str,
        code: str,
        version: str = "0.1.0",
        description: str = "",
    ) -> DynamicPythonPlugin:
        """Create a live in-memory plugin by executing raw Python code in a namespace."""
        _, tools = _compile_dynamic_module(name, code)
        return DynamicPythonPlugin(
            name=name,
            version=version,
            description=description,
            tools=tools,
            code=code,
        )

    @staticmethod
    def scaffold_project(
        target_dir: Path,
        name: str,
        description: str = "",
        language: str = "python",
        tools: list[str] | None = None,
        dependencies: list[str] | None = None,
        author: str = "Harness Developer",
        category: str = "general",
        preset: str = "general",
        isolation: IsolationMode = IsolationMode.SUBPROCESS,
        tags: list[str] | None = None,
    ) -> Path:
        """Scaffold a new plugin project directory (delegates to PluginCreator)."""
        from harness.creator.creator import PluginCreator

        res = PluginCreator.scaffold(
            target_dir=target_dir,
            name=name,
            description=description,
            language=language,
            tools=tools or ["execute"],
            dependencies=dependencies or [],
            author=author,
            category=category,
            preset=preset,
            isolation=isolation,
            tags=tags or [],
        )
        return res.path

    @staticmethod
    async def validate_project(
        target_dir: Path | str,
        *,
        dry_run: bool = False,
        timeout: float = 15.0,
        remediate: bool = False,
    ) -> Any:
        """Validate a plugin project directory using PluginCreator."""
        from harness.creator.creator import PluginCreator

        return await PluginCreator.validate(target_dir, dry_run=dry_run, timeout=timeout, remediate=remediate)

    @staticmethod
    async def from_zip(
        zip_path: Path | str,
        target_dir: Path | None = None,
    ) -> HarnessPlugin:
        """Create a live SandboxedPlugin from a ZIP archive via PluginCreator."""
        from harness.creator.creator import PluginCreator

        return await PluginCreator.from_zip(zip_path, target_dir=target_dir)

    @staticmethod
    async def from_github(
        source: str,
        *,
        ref: str = "main",
        github_token: str | None = None,
        target_dir: Path | None = None,
    ) -> HarnessPlugin:
        """Create a live SandboxedPlugin from a GitHub repository via PluginCreator."""
        from harness.creator.creator import PluginCreator

        return await PluginCreator.from_github(source, ref=ref, github_token=github_token, target_dir=target_dir)


__all__ = [
    "DynamicPluginBuilder",
    "DynamicPythonPlugin",
    "RuntimeIntrospector",
    "_compile_dynamic_module",
]
