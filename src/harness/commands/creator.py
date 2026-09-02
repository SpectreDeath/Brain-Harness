"""Plugin creator commands — pure async functions for unified plugin and skill synthesis and validation."""

from __future__ import annotations

from pathlib import Path

from harness.creator.creator import PluginCreator
from harness.creator.scaffold import ScaffoldOptions, ScaffoldResult
from harness.creator.synthesis import (
    PluginSynthesisEngine,
    SynthesisMode,
    SynthesisRequest,
    SynthesisResult,
)
from harness.creator.validator import ValidationReport
from harness.plugins.manifest import IsolationMode

_SYNTHESIS_ENGINE = PluginSynthesisEngine()


async def synthesize_plugin_cmd(request: SynthesisRequest) -> SynthesisResult:
    """Synthesize a new plugin or skill using the unified PluginSynthesisEngine."""
    return await _SYNTHESIS_ENGINE.synthesize(request)


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
    return await _SYNTHESIS_ENGINE.validate(
        path,
        dry_run=dry_run,
        remediate=remediate,
    )


def list_archetypes_cmd() -> list[dict[str, str]]:
    """List all available plugin archetype presets and descriptions."""
    return _SYNTHESIS_ENGINE.list_archetypes()


async def remediate_plugin_cmd(path: Path | str = ".") -> ValidationReport:
    """Auto-repair missing manifest, boilerplate functions, and dependency files."""
    return await _SYNTHESIS_ENGINE.validate(path, remediate=True)


# Backward-compatible alias
build_plugin_cmd = scaffold_plugin_cmd


# --- Click CLI adapters ---
import click
from harness.commands._utils import _run_async


@click.group("creator")
def creator_group() -> None:
    """Creator Mode tools for plugin authoring."""


@creator_group.command("build")
@click.argument("name")
@click.option("--description", "-d", default="", help="Plugin description")
@click.option("--target-dir", default=None, help="Output directory")
@click.option(
    "--language",
    "-l",
    default="python",
    type=click.Choice(["python", "javascript", "typescript"], case_sensitive=False),
    help="Implementation language",
)
@click.option("--tools", "-t", default="execute", help="Comma-separated tool handler names")
@click.option("--deps", default="", help="Comma-separated external dependencies")
@click.option(
    "--isolation",
    "-i",
    default="subprocess",
    type=click.Choice(["subprocess", "venv", "in_process", "docker"], case_sensitive=False),
    help="Sandbox isolation mode",
)
@click.option("--category", "-c", default="general", help="Domain category")
@click.option(
    "--preset",
    "-p",
    default="general",
    type=click.Choice(["general", "tool", "service", "api_wrapper", "agentic_workflow", "container", "mcp_bridge"], case_sensitive=False),
    help="Plugin archetype preset",
)
@click.option("--author", "-a", default="Harness Developer", help="Plugin author")
def creator_build(
    name: str,
    description: str,
    target_dir: str | None,
    language: str,
    tools: str,
    deps: str,
    isolation: str,
    category: str,
    preset: str,
    author: str,
) -> None:
    """Scaffold a new plugin project."""
    out_dir = Path(target_dir) if target_dir else Path("plugins") / name
    tools_list = [t.strip() for t in tools.split(",") if t.strip()]
    deps_list = [d.strip() for d in deps.split(",") if d.strip()]

    _run_async(
        scaffold_plugin_cmd(
            name=name,
            target_dir=out_dir,
            description=description,
            language=language,
            tools=tools_list,
            dependencies=deps_list,
            author=author,
            category=category,
            preset=preset,
            isolation=isolation,
        )
    )
    click.echo(f"✓ Created plugin scaffold at {out_dir}")
    click.echo(f"  ├── plugin.json (language: {language}, isolation: {isolation})")
    main_file = "main.py" if language == "python" else ("index.ts" if language == "typescript" else "index.js")
    click.echo(f"  ├── {main_file}")
    click.echo("  └── QUICKSTART.md")


creator_group.add_command(creator_build, name="scaffold")


@creator_group.command("init")
def creator_init() -> None:
    """Interactive wizard for scaffolding a new plugin project."""
    click.echo("🚀 Brain Harness — Plugin Creator Wizard")
    click.echo("━" * 45)

    name = click.prompt("Plugin Name (e.g. data_cleaner)", type=str)
    description = click.prompt("Description", default=f"Plugin providing {name} tools", type=str)
    language = click.prompt(
        "Language",
        default="python",
        type=click.Choice(["python", "javascript", "typescript"], case_sensitive=False),
    )
    preset = click.prompt(
        "Archetype Preset",
        default="general",
        type=click.Choice(["general", "tool", "service", "api_wrapper", "agentic_workflow", "container", "mcp_bridge"], case_sensitive=False),
    )
    tools_raw = click.prompt("Tools (comma-separated)", default="execute", type=str)
    deps_raw = click.prompt("Dependencies (comma-separated)", default="", show_default=False, type=str)
    isolation = click.prompt(
        "Isolation Mode",
        default="subprocess",
        type=click.Choice(["subprocess", "venv", "in_process", "docker"], case_sensitive=False),
    )
    category = click.prompt("Category", default="general", type=str)
    default_dir = f"plugins/{name}"
    target_dir = click.prompt("Target Directory", default=default_dir, type=str)

    tools_list = [t.strip() for t in tools_raw.split(",") if t.strip()]
    deps_list = [d.strip() for d in deps_raw.split(",") if d.strip()]
    out_dir = Path(target_dir)

    _run_async(
        scaffold_plugin_cmd(
            name=name,
            target_dir=out_dir,
            description=description,
            language=language,
            tools=tools_list,
            dependencies=deps_list,
            category=category,
            preset=preset,
            isolation=isolation,
        )
    )
    click.echo(f"\n✓ Successfully initialized plugin '{name}' at {out_dir}")


@creator_group.command("validate")
@click.argument("plugin_path", default=".")
@click.option("--dry-run", is_flag=True, default=False, help="Boot sandbox and execute entrypoints")
@click.option("--timeout", default=15.0, help="Sandbox dry-run timeout in seconds")
@click.option("--fix", "--remediate", "remediate", is_flag=True, default=False, help="Automatically repair detected issues")
def creator_validate(plugin_path: str, dry_run: bool, timeout: float, remediate: bool) -> None:
    """Validate a plugin manifest, source files, and sandbox execution."""
    report = _run_async(validate_plugin_cmd(plugin_path, dry_run=dry_run, timeout=timeout, remediate=remediate))
    click.echo(report.format_cli())
    if not report.valid:
        raise click.ClickException("Validation failed. See details above.")


@creator_group.command("remediate")
@click.argument("plugin_path", default=".")
def creator_remediate(plugin_path: str) -> None:
    """Auto-repair missing manifest, boilerplate functions, and dependency files."""
    report = _run_async(remediate_plugin_cmd(plugin_path))
    click.echo(report.format_cli())
    if report.valid:
        click.echo("✓ Successfully auto-remediated plugin package.")
    else:
        raise click.ClickException("Remediation completed with remaining errors.")


@creator_group.command("archetypes")
def creator_archetypes() -> None:
    """List all available plugin archetypes and templates."""
    archetypes = list_archetypes_cmd()
    click.echo("📦 Available Plugin Archetypes")
    click.echo("━" * 45)
    for a in archetypes:
        click.echo(f"  • {a['name']:<18} — {a['description']}")


__all__ = [
    "build_plugin_cmd",
    "creator_archetypes",
    "creator_build",
    "creator_group",
    "creator_init",
    "creator_remediate",
    "creator_validate",
    "list_archetypes_cmd",
    "remediate_plugin_cmd",
    "scaffold_plugin_cmd",
    "synthesize_plugin_cmd",
    "validate_plugin_cmd",
]
