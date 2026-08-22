"""Plugin creator commands — pure async functions for plugin scaffolding and validation."""

from __future__ import annotations

from pathlib import Path

from harness.creator.creator import PluginCreator
from harness.creator.scaffold import ScaffoldOptions, ScaffoldResult
from harness.creator.validator import ValidationReport
from harness.plugins.manifest import IsolationMode


async def scaffold_plugin_cmd(
    name: str,
    target_dir: Path | str | None = None,
    *,
    description: str = "",
    language: str = "python",
    preset: str = "general",
    tools: list[str] | None = None,
    dependencies: list[str] | None = None,
    author: str = "Harness Developer",
    category: str = "general",
    isolation: str = "subprocess",
    tags: list[str] | None = None,
    auto_validate: bool = False,
) -> ScaffoldResult:
    """Scaffold a new plugin project directory asynchronously."""
    out_dir = Path(target_dir) if target_dir else Path("plugins") / name
    options = ScaffoldOptions(
        name=name,
        description=description,
        language=language.lower(),
        preset=preset.lower(),
        tools=tools or ["execute"],
        dependencies=dependencies or [],
        author=author,
        category=category,
        isolation=IsolationMode(isolation.lower()),
        tags=tags or [],
        auto_validate=auto_validate,
    )
    return await PluginCreator.scaffold_async(out_dir, options=options)


async def validate_plugin_cmd(
    path: Path | str,
    *,
    dry_run: bool = False,
    timeout: float = 15.0,
    remediate: bool = False,
) -> ValidationReport:
    """Validate a plugin project directory with optional auto-remediation."""
    return await PluginCreator.validate(
        path,
        dry_run=dry_run,
        timeout=timeout,
        remediate=remediate,
    )


def list_archetypes_cmd() -> list[dict[str, str]]:
    """List all available plugin archetype presets and descriptions."""
    return PluginCreator.list_archetypes()


__all__ = [
    "list_archetypes_cmd",
    "scaffold_plugin_cmd",
    "validate_plugin_cmd",
]
