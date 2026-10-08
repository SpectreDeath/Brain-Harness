"""Factory and single-seam resolver for dynamic in-memory and on-disk plugins."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from harness.creator.dynamic.compiler import _compile_dynamic_module
from harness.creator.dynamic.plugin import DynamicPythonPlugin
from harness.plugins.base import HarnessPlugin
from harness.plugins.manifest import IsolationMode


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


def resolve_dynamic_builder(context: Any = None) -> type[DynamicPluginBuilder] | DynamicPluginBuilder:
    """Single-seam resolver for DynamicPluginBuilder factory (Rule 58).

    Resolves configured builder from IoC container if registered, otherwise
    falls back to the authoritative DynamicPluginBuilder class.
    """
    if context is not None:
        try:
            from harness.services.keys import CREATOR_SERVICE_KEY

            creator = context.optional(CREATOR_SERVICE_KEY)
            if creator is not None and hasattr(creator, "dynamic_builder"):
                return creator.dynamic_builder  # type: ignore[no-any-return]
        except Exception:
            pass
    return DynamicPluginBuilder
