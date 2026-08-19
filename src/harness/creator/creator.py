"""Plugin Creator — authoritative unified facade for plugin authoring and lifecycle.

Consolidates:
    - Scaffolding (sync & async across Python, JavaScript, TypeScript)
    - Dynamic in-memory plugin synthesis and live hot-reloading
    - Deep AST type and schema inference
    - Diagnostic validation and automated remediation
    - External ingestion (ZIP, GitHub)
    - Runtime dependency and lifecycle introspection
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import structlog

from harness.creator.archetypes import ArchetypeRegistry, PluginArchetype
from harness.creator.dynamic import DynamicPythonPlugin
from harness.creator.introspection import RuntimeIntrospector
from harness.creator.scaffold import (
    PluginScaffoldEngine,
    ScaffoldOptions,
    ScaffoldResult,
)
from harness.creator.schema import SchemaInferrer
from harness.creator.validator import (
    PluginValidator,
    ValidationPipeline,
    ValidationReport,
)
from harness.kernel.context import ServiceContext
from harness.kernel.lifecycle import PluginLifecycle
from harness.plugins.base import HarnessPlugin
from harness.plugins.manifest import IsolationMode, PluginManifest
from harness.services.tools import ToolRegistry

logger = structlog.get_logger()


class PluginCreator:
    """Authoritative, high-leverage facade for all plugin authoring operations in Harness."""

    # 1. Scaffolding & Project Generation
    @classmethod
    def scaffold(
        cls,
        target_dir: Path | str,
        options: ScaffoldOptions | None = None,
        *,
        name: str | None = None,
        description: str = "",
        language: str = "python",
        tools: list[str] | None = None,
        dependencies: list[str] | None = None,
        author: str = "Harness Developer",
        category: str = "general",
        preset: str = "general",
        isolation: IsolationMode = IsolationMode.SUBPROCESS,
        tags: list[str] | None = None,
        auto_validate: bool = False,
        templates_dir: Path | None = None,
    ) -> ScaffoldResult:
        """Scaffold a new plugin project directory synchronously."""
        out_dir = Path(target_dir).resolve()
        engine = PluginScaffoldEngine(templates_dir=templates_dir)
        opts = options or ScaffoldOptions(
            name=name or out_dir.name,
            description=description,
            language=language,
            tools=tools or ["execute"],
            dependencies=dependencies or [],
            author=author,
            category=category,
            preset=preset,
            isolation=isolation,
            tags=tags or [],
            auto_validate=auto_validate,
        )
        return engine.scaffold(out_dir, options=opts)

    @classmethod
    async def scaffold_async(
        cls,
        target_dir: Path | str,
        options: ScaffoldOptions | None = None,
        *,
        name: str | None = None,
        description: str = "",
        language: str = "python",
        tools: list[str] | None = None,
        dependencies: list[str] | None = None,
        author: str = "Harness Developer",
        category: str = "general",
        preset: str = "general",
        isolation: IsolationMode = IsolationMode.SUBPROCESS,
        tags: list[str] | None = None,
        auto_validate: bool = False,
        templates_dir: Path | None = None,
    ) -> ScaffoldResult:
        """Scaffold a new plugin project directory asynchronously."""
        out_dir = Path(target_dir).resolve()
        engine = PluginScaffoldEngine(templates_dir=templates_dir)
        opts = options or ScaffoldOptions(
            name=name or out_dir.name,
            description=description,
            language=language,
            tools=tools or ["execute"],
            dependencies=dependencies or [],
            author=author,
            category=category,
            preset=preset,
            isolation=isolation,
            tags=tags or [],
            auto_validate=auto_validate,
        )
        return await engine.scaffold_async(out_dir, options=opts)

    @classmethod
    async def scaffold_and_mount(
        cls,
        runtime: Any,
        target_dir: Path | str,
        options: ScaffoldOptions | None = None,
        *,
        auto_enable: bool = True,
        **kwargs: Any,
    ) -> tuple[ScaffoldResult, HarnessPlugin]:
        """Scaffold a plugin project and immediately mount/load it into a live HarnessRuntime."""
        result = await cls.scaffold_async(target_dir, options=options, **kwargs)
        plugin = await runtime.add_plugin_from_source(result.path, auto_enable=auto_enable)
        logger.info(
            "Scaffolded and mounted plugin onto runtime",
            name=plugin.name,
            path=str(result.path),
            auto_enable=auto_enable,
        )
        return result, plugin

    # 2. Dynamic In-Memory Synthesis
    @classmethod
    def from_functions(
        cls,
        name: str,
        functions: list[Callable[..., Any]],
        *,
        version: str = "0.1.0",
        description: str = "",
    ) -> DynamicPythonPlugin:
        """Create a live in-memory plugin from a list of typed Python callables."""
        tools_dict = {fn.__name__: fn for fn in functions}
        return DynamicPythonPlugin(
            name=name,
            version=version,
            description=description,
            tools=tools_dict,
        )

    @classmethod
    def from_code(
        cls,
        name: str,
        code: str,
        *,
        version: str = "0.1.0",
        description: str = "",
    ) -> DynamicPythonPlugin:
        """Create a live in-memory plugin by executing raw Python source code."""
        import types

        module = types.ModuleType(f"dynamic_plugin_{name}")
        exec(code, module.__dict__)  # noqa: S102

        tools: dict[str, Callable[..., Any]] = {}
        for attr_name in dir(module):
            if not attr_name.startswith("_"):
                attr = getattr(module, attr_name)
                if callable(attr):
                    tools[attr_name] = attr

        return DynamicPythonPlugin(
            name=name,
            version=version,
            description=description,
            tools=tools,
            code=code,
        )

    # 3. Validation & Remediation
    @classmethod
    async def validate(
        cls,
        plugin_dir: Path | str,
        *,
        dry_run: bool = False,
        timeout: float = 15.0,
        remediate: bool = False,
        pipeline: ValidationPipeline | None = None,
    ) -> ValidationReport:
        """Execute diagnostic validation rules on a plugin project."""
        return await PluginValidator.validate(
            plugin_dir,
            dry_run=dry_run,
            timeout=timeout,
            remediate=remediate,
            pipeline=pipeline,
        )

    @classmethod
    def validate_sync(
        cls,
        plugin_dir: Path | str,
        *,
        dry_run: bool = False,
        timeout: float = 15.0,
        remediate: bool = False,
        pipeline: ValidationPipeline | None = None,
    ) -> ValidationReport:
        """Synchronously execute diagnostic validation checks on a plugin project."""
        return PluginValidator.validate_sync(
            plugin_dir,
            dry_run=dry_run,
            timeout=timeout,
            remediate=remediate,
            pipeline=pipeline,
        )

    @classmethod
    async def remediate(cls, plugin_dir: Path | str) -> ValidationReport:
        """Auto-remediate missing files, stubs, and dependencies in a plugin project."""
        return await PluginValidator.remediate(plugin_dir)

    # 4. External Ingestion
    @classmethod
    async def from_zip(
        cls,
        zip_path: Path | str,
        target_dir: Path | None = None,
    ) -> HarnessPlugin:
        """Ingest and instantiate a plugin package from a ZIP archive."""
        from harness.ingestion.pipeline import PluginIngestionPipeline

        pipeline = PluginIngestionPipeline(plugin_dir=target_dir)
        return await pipeline.ingest(str(zip_path))

    @classmethod
    async def from_github(
        cls,
        source: str,
        *,
        ref: str = "main",
        github_token: str | None = None,
        target_dir: Path | None = None,
    ) -> HarnessPlugin:
        """Fetch, convert, and instantiate a plugin from a GitHub repository."""
        from harness.ingestion.pipeline import PluginIngestionPipeline

        pipeline = PluginIngestionPipeline(plugin_dir=target_dir, github_token=github_token)
        return await pipeline.ingest(source, ref=ref)

    # 5. Schema Inference & Archetypes
    @classmethod
    def infer_manifest(
        cls,
        name: str,
        tools: dict[str, Callable[..., Any]] | list[Callable[..., Any]],
        *,
        version: str = "0.1.0",
        description: str = "",
        category: str = "general",
        preset: str = "general",
        isolation: IsolationMode = IsolationMode.SUBPROCESS,
        author: str = "Harness Developer",
        tags: list[str] | None = None,
        dependencies: list[str] | None = None,
    ) -> PluginManifest:
        """Infer a complete PluginManifest using deep reflection over callables."""
        return SchemaInferrer.infer_manifest(
            name=name,
            tools=tools,
            version=version,
            description=description,
            category=category,
            preset=preset,
            isolation=isolation,
            author=author,
            tags=tags,
            dependencies=dependencies,
        )

    @classmethod
    def list_archetypes(cls) -> list[dict[str, str]]:
        """List all registered plugin archetypes."""
        return ArchetypeRegistry.list_archetypes()

    @classmethod
    def get_archetype(cls, name: str) -> PluginArchetype:
        """Retrieve a specific plugin archetype preset."""
        return ArchetypeRegistry.get(name)

    @classmethod
    def register_archetype(cls, archetype: PluginArchetype | type[PluginArchetype]) -> None:
        """Register a custom archetype strategy in the registry."""
        ArchetypeRegistry.register(archetype)

    @classmethod
    def unregister_archetype(cls, name: str) -> bool:
        """Unregister an archetype preset from the registry."""
        return ArchetypeRegistry.unregister(name)

    @classmethod
    def has_archetype(cls, name: str) -> bool:
        """Check if an archetype preset exists in the registry."""
        return ArchetypeRegistry.has(name)

    # 6. Introspection & Graphing
    @classmethod
    def introspect(
        cls,
        context: ServiceContext,
        lifecycle: PluginLifecycle,
        tool_registry: ToolRegistry | None = None,
    ) -> RuntimeIntrospector:
        """Create a runtime introspector for live system topology analysis."""
        return RuntimeIntrospector(
            context=context,
            lifecycle=lifecycle,
            tool_registry=tool_registry,
        )


__all__ = ["PluginCreator"]
