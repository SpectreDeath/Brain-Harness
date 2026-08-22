"""CLI entry point — simple commands for managing the harness.

Commands:
    harness init                      Initialize a workspace
    harness plugin add <url>          Fetch, inspect, and register a GitHub repo
    harness plugin list               List all installed plugins
    harness plugin enable <name>      Enable a plugin
    harness plugin disable <name>     Disable a plugin
    harness plugin remove <name>      Remove a cached plugin
    harness events [--type TYPE]      Show the event log
    harness services                  List registered services
    harness run                       Start the harness (interactive)
    harness agent run "<task>"        Execute an autonomous agent task
    harness introspect                Show live system diagnostics & graph
    harness bridge status             Check ecosystem bridges
    harness creator build <name>      Scaffold a new plugin project
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import click
import structlog

logger = structlog.get_logger()


def _run_async(coro: Any) -> Any:
    """Run an async coroutine from sync CLI context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


@click.group()
@click.version_option(version="0.1.0", prog_name="harness")
@click.option("--debug", is_flag=True, help="Enable verbose debug logging")
def main(debug: bool) -> None:
    """Harness — Modular agent harness where everything is a plugin."""
    if sys.platform == "win32":
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    import logging
    log_level = logging.DEBUG if debug else logging.WARNING

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )


@main.command()
@click.argument("path", default=".", type=click.Path())
def init(path: str) -> None:
    """Initialize a harness workspace."""
    workspace = Path(path).resolve()
    plugins_dir = workspace / "plugins"
    config_dir = workspace / ".harness"

    plugins_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    # Create default config
    config_file = config_dir / "config.json"
    if not config_file.exists():
        config = {
            "version": "0.1.0",
            "plugin_dirs": ["plugins"],
            "event_log": ".harness/events.jsonl",
            "storage_db": ".harness/storage.db",
        }
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    click.echo(f"✓ Workspace initialized at {workspace}")
    click.echo("  plugins/          → Drop-in plugin directory")
    click.echo("  .harness/         → Configuration and data")
    click.echo("\nNext: harness plugin add <github-url>")


@main.group()
def plugin() -> None:
    """Manage plugins."""


@plugin.command("add")
@click.argument("source")
@click.option("--ref", default="main", help="Git ref (branch/tag) to fetch")
@click.option("--force", is_flag=True, help="Re-download even if cached")
@click.option("--token", envvar="GITHUB_TOKEN", help="GitHub API token")
def plugin_add(source: str, ref: str, force: bool, token: str | None) -> None:
    """Fetch a GitHub repository and register it as a plugin.

    SOURCE can be a GitHub URL, owner/repo shorthand, or local ZIP path.
    """
    from harness.commands.plugins import add_plugin

    click.echo(f"⟳ Ingesting plugin from {source}...")
    plugin, manifest = _run_async(add_plugin(source, ref=ref, force=force, token=token))

    if manifest:
        click.echo(f"  ✓ Manifest: {manifest.name}@{manifest.version}")
        click.echo(f"    Language:    {manifest.language}")
        click.echo(f"    Entrypoint:  {manifest.entrypoint or '(auto-detect)'}")
        click.echo(f"    Isolation:   {manifest.isolation.value}")
        click.echo(f"    Entrypoints: {len(manifest.entrypoints)} functions found")

        if manifest.dependencies:
            click.echo(f"    Dependencies: {', '.join(manifest.dependencies[:5])}")
            if len(manifest.dependencies) > 5:
                click.echo(f"      ... and {len(manifest.dependencies) - 5} more")

    click.echo(f"\n✓ Plugin '{plugin.name}' added successfully!")
    click.echo("  Run 'harness plugin list' to see all plugins")


@plugin.command("list")
def plugin_list() -> None:
    """List all installed plugins."""
    from harness.commands.plugins import list_plugins

    cached = list_plugins()

    if not cached:
        click.echo("No plugins installed.")
        click.echo("Run 'harness plugin add <github-url>' to add one.")
        return

    click.echo(f"{'Name':<30} {'Manifest':<12} {'Path'}")
    click.echo("─" * 80)
    for entry in cached:
        has_manifest = "✓" if entry["has_manifest"] else "✗"
        click.echo(f"{entry['name']:<30} {has_manifest:<12} {entry['path']}")

    click.echo(f"\nTotal: {len(cached)} plugin(s)")


@plugin.command("remove")
@click.argument("name")
@click.confirmation_option(prompt="Are you sure you want to remove this plugin?")
def plugin_remove(name: str) -> None:
    """Remove a cached plugin."""
    from harness.commands.plugins import remove_plugin

    if remove_plugin(name):
        click.echo(f"✓ Removed plugin '{name}'")
    else:
        click.echo(f"✗ Plugin '{name}' not found")


@plugin.command("inspect")
@click.argument("source")
def plugin_inspect(source: str) -> None:
    """Inspect a plugin directory and show its manifest card."""
    from harness.commands.plugins import inspect_plugin

    try:
        manifest = inspect_plugin(source)
    except FileNotFoundError:
        click.echo(f"✗ Not found: {source}")
        return

    click.echo(manifest.format_card())


@plugin.command("info")
@click.argument("name")
def plugin_info(name: str) -> None:
    """Show the standardized summary card for an installed plugin."""
    from harness.commands.plugins import get_plugin_manifest

    manifest = get_plugin_manifest(name)
    if not manifest:
        click.echo(f"✗ Plugin '{name}' not found")
        return

    click.echo(manifest.format_card())
    if manifest.entrypoints:
        click.echo("\nSample Skills / Tools:")
        for ep in manifest.entrypoints[:10]:
            params = ", ".join(p.name for p in ep.parameters)
            click.echo(f"  * {ep.name}({params})")
            if ep.description:
                click.echo(f"      {ep.description[:80]}")
    click.echo("\nRun 'harness plugin guide " + name + "' to view the Quick Start Guide")


@plugin.command("card")
@click.argument("name")
def plugin_card(name: str) -> None:
    """Show the standardized summary card for an installed plugin."""
    from harness.commands.plugins import get_plugin_manifest

    manifest = get_plugin_manifest(name)
    if not manifest:
        click.echo(f"✗ Plugin '{name}' not found")
        return
    click.echo(manifest.format_card())


@plugin.command("guide")
@click.argument("name")
def plugin_guide(name: str) -> None:
    """Show the Quick Start and Agent Usage Guide for an installed plugin."""
    from harness.commands.plugins import get_plugin_guide

    result = get_plugin_guide(name)
    if not result:
        click.echo(f"✗ Plugin '{name}' not found")
        return

    manifest, guide = result
    click.echo(guide)


@plugin.command("enable")
@click.argument("name")
def plugin_enable(name: str) -> None:
    """Enable a plugin by name or pattern."""
    from harness.commands.plugins import enable_plugin_by_name

    matched = _run_async(enable_plugin_by_name(name))
    if matched:
        for pname in matched:
            click.echo(f"✓ Enabled plugin '{pname}'")
    else:
        click.echo(f"✗ Plugin '{name}' not found")


@plugin.command("disable")
@click.argument("name")
def plugin_disable(name: str) -> None:
    """Disable a plugin by name or pattern."""
    from harness.commands.plugins import disable_plugin_by_name

    matched = _run_async(disable_plugin_by_name(name))
    if matched:
        for pname in matched:
            click.echo(f"✓ Disabled plugin '{pname}'")
    else:
        click.echo(f"✗ Plugin '{name}' not found")


@plugin.command("enable-all")
def plugin_enable_all() -> None:
    """Enable all discovered plugins."""
    from harness.commands.plugins import enable_all_plugins

    results = _run_async(enable_all_plugins())
    click.echo(f"✓ Enabled {sum(results.values())}/{len(results)} plugins")


@plugin.command("disable-all")
@click.option("--keep-core/--all", default=True, help="Keep core infrastructure services active")
def plugin_disable_all(keep_core: bool) -> None:
    """Disable all active plugins."""
    from harness.commands.plugins import disable_all_plugins

    disabled = _run_async(disable_all_plugins(keep_core=keep_core))
    click.echo(f"✓ Disabled {len(disabled)} plugins")


@main.group()
def tool() -> None:
    """Inspect and manage granular tool and skill enablement."""


@tool.command("list")
@click.option("--provider", help="Filter tools by provider plugin name")
@click.option("--enabled-only", is_flag=True, help="Only list currently enabled tools")
def tool_list(provider: str | None, enabled_only: bool) -> None:
    """List all registered tools with their active status."""
    from harness.commands.tools import list_tools_summary

    tools = _run_async(list_tools_summary(provider=provider, enabled_only=enabled_only))
    if not tools:
        click.echo("No tools found.")
        return

    click.echo(f"{'Tool Name':<38} {'Status':<10} {'Provider'}")
    click.echo("─" * 75)
    for t in tools:
        status_str = "✓ Enabled" if t["enabled"] else "✗ Disabled"
        click.echo(f"{t['name']:<38} {status_str:<10} {t['provider']}")
    click.echo(f"\nTotal: {len(tools)} tool(s)")


@tool.command("enable")
@click.argument("name")
def tool_enable(name: str) -> None:
    """Enable a specific tool by name."""
    from harness.commands.tools import enable_tool_by_name

    matched = _run_async(enable_tool_by_name(name))
    if matched:
        for tname in matched:
            click.echo(f"✓ Enabled tool '{tname}'")
    else:
        click.echo(f"✗ Tool '{name}' not found")


@tool.command("disable")
@click.argument("name")
def tool_disable(name: str) -> None:
    """Disable a specific tool by name."""
    from harness.commands.tools import disable_tool_by_name

    matched = _run_async(disable_tool_by_name(name))
    if matched:
        for tname in matched:
            click.echo(f"✓ Disabled tool '{tname}'")
    else:
        click.echo(f"✗ Tool '{name}' not found")


@main.group()
def bridge() -> None:
    """Inspect and manage ecosystem bridges (Em-Cubed, Memtext, Skill Flywheel)."""


@bridge.command("status")
def bridge_status() -> None:
    """Check discovery status of peer ecosystem repositories."""
    from harness.bridges.base import EcosystemBridgeCatalog

    status_map = EcosystemBridgeCatalog.status()
    click.echo(f"{'Ecosystem Component':<20} {'Status':<15} {'Override Env Var':<22} {'Path'}")
    click.echo("─" * 85)
    for name, info in status_map.items():
        st = "✓ Available" if info["available"] else "✗ Not found"
        p = info["path"] or "(not discovered)"
        click.echo(f"{name:<20} {st:<15} {info['env_var']:<22} {p}")


@main.command()
def services() -> None:
    """List registered services and their provider plugins."""
    from harness.commands.system import list_services

    srvs = _run_async(list_services())
    if not srvs:
        click.echo("No services registered.")
        return

    click.echo(f"{'Service Key':<35} {'Provider Plugin'}")
    click.echo("─" * 65)
    for key_name, provider in sorted(srvs.items()):
        prov_str = provider or "core"
        click.echo(f"{key_name:<35} {prov_str}")

    click.echo(f"\nTotal: {len(srvs)} registered service(s)")


@main.command()
@click.option("--type", "event_type", default=None, help="Filter by event type")
@click.option("--limit", default=50, help="Max events to show")
def events(event_type: str | None, limit: int) -> None:
    """Show the event log."""
    from harness.events.bus import EventBus

    log_path = Path(".harness") / "events.jsonl"
    if not log_path.exists():
        click.echo("No event log found. Initialize with 'harness init' first.")
        return

    evts = EventBus.read_log_file(log_path, event_type=event_type, limit=limit)
    if not evts:
        click.echo("No events found.")
        return

    for evt in evts:
        ts = evt.timestamp.isoformat()[:19]
        etype = evt.event_type.value
        source = evt.source
        click.echo(f"  {ts}  [{etype}]  {source}")

    click.echo(f"\nShowing {len(evts)} event(s)")


@main.group()
def agent() -> None:
    """Run and manage autonomous agent loops."""


@agent.command("run")
@click.argument("task")
@click.option("--max-steps", default=10, help="Maximum thought/action steps")
def agent_run(task: str, max_steps: int) -> None:
    """Execute an autonomous task using the active agent loop."""
    from harness.commands.agent import run_agent

    click.echo(f"🤖 Starting agent task: {task}")
    result = _run_async(run_agent(task, max_steps=max_steps))

    click.echo(f"Status: {result.status}")
    click.echo(f"Steps:  {len(result.steps)}")
    click.echo(f"Result: {result.final_answer}")


@main.group()
def creator() -> None:
    """Creator Mode tools for plugin authoring."""


@creator.command("build")
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
    from harness.creator.creator import PluginCreator
    from harness.plugins.manifest import IsolationMode

    out_dir = Path(target_dir) if target_dir else Path("plugins") / name
    tools_list = [t.strip() for t in tools.split(",") if t.strip()]
    deps_list = [d.strip() for d in deps.split(",") if d.strip()]

    PluginCreator.scaffold(
        target_dir=out_dir,
        name=name,
        description=description,
        language=language.lower(),
        tools=tools_list,
        dependencies=deps_list,
        author=author,
        category=category,
        preset=preset.lower(),
        isolation=IsolationMode(isolation.lower()),
    )
    click.echo(f"✓ Created plugin scaffold at {out_dir}")
    click.echo(f"  ├── plugin.json (language: {language}, isolation: {isolation})")
    main_file = "main.py" if language == "python" else ("index.ts" if language == "typescript" else "index.js")
    click.echo(f"  ├── {main_file}")
    click.echo("  └── QUICKSTART.md")


creator.add_command(creator_build, name="scaffold")


@creator.command("init")
def creator_init() -> None:
    """Interactive wizard for scaffolding a new plugin project."""
    from harness.creator.creator import PluginCreator
    from harness.plugins.manifest import IsolationMode

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

    PluginCreator.scaffold(
        target_dir=out_dir,
        name=name,
        description=description,
        language=language.lower(),
        tools=tools_list,
        dependencies=deps_list,
        category=category,
        preset=preset.lower(),
        isolation=IsolationMode(isolation.lower()),
    )
    click.echo(f"\n✓ Successfully initialized plugin '{name}' at {out_dir}")


@creator.command("validate")
@click.argument("plugin_path", default=".")
@click.option("--dry-run", is_flag=True, default=False, help="Boot sandbox and execute entrypoints")
@click.option("--timeout", default=15.0, help="Sandbox dry-run timeout in seconds")
@click.option("--fix", "--remediate", "remediate", is_flag=True, default=False, help="Automatically repair detected issues")
def creator_validate(plugin_path: str, dry_run: bool, timeout: float, remediate: bool) -> None:
    """Validate a plugin manifest, source files, and sandbox execution."""
    from harness.creator.creator import PluginCreator

    report = _run_async(PluginCreator.validate(plugin_path, dry_run=dry_run, timeout=timeout, remediate=remediate))
    click.echo(report.format_cli())
    if not report.valid:
        raise click.ClickException("Validation failed. See details above.")


@creator.command("remediate")
@click.argument("plugin_path", default=".")
def creator_remediate(plugin_path: str) -> None:
    """Auto-repair missing manifest, boilerplate functions, and dependency files."""
    from harness.creator.creator import PluginCreator

    report = _run_async(PluginCreator.remediate(plugin_path))
    click.echo(report.format_cli())
    if report.valid:
        click.echo("✓ Successfully auto-remediated plugin package.")
    else:
        raise click.ClickException("Remediation completed with remaining errors.")


@creator.command("archetypes")
def creator_archetypes() -> None:
    """List all available plugin archetypes and templates."""
    from harness.creator.creator import PluginCreator

    archetypes = PluginCreator.list_archetypes()
    click.echo("📦 Available Plugin Archetypes")
    click.echo("━" * 45)
    for a in archetypes:
        click.echo(f"  • {a['name']:<18} — {a['description']}")


# Register top-level aliases for rapid creator access
main.add_command(creator_build, name="create")
main.add_command(creator_build, name="scaffold")
main.add_command(creator_validate, name="validate")
main.add_command(creator_archetypes, name="archetypes")


@main.command()
def introspect() -> None:
    """Display runtime system diagnostics and dependency graph."""
    from harness.commands.system import run_introspect

    report = _run_async(run_introspect())

    click.echo("🔍 System Introspection Report")
    click.echo("━" * 40)
    click.echo(f"Active Plugins ({report['plugins_count']}):")
    for p, s in report["plugins"].items():
        click.echo(f"  • {p:<25} [{s}]")

    click.echo(f"\nRegistered Services ({report['services_count']}):")
    for s, prov in report["services"].items():
        click.echo(f"  • {s:<25} (provided by: {prov})")

    click.echo(f"\nAvailable Tools ({report['tools_count']}):")
    for t in report["tools"]:
        click.echo(f"  • {t}")

    click.echo("\n📊 Mermaid Dependency Graph:")
    click.echo(report["graph"])


@main.command()
def run() -> None:
    """Start the harness (interactive mode)."""
    click.echo("🔧 Harness v0.1.0")
    click.echo("━" * 40)

    async def _run() -> None:
        from harness.kernel.runtime import HarnessRuntime

        event_log = Path(".harness") / "events.jsonl"
        click.echo("⟳ Loading built-in and ecosystem plugins...")

        runtime = HarnessRuntime.create(
            event_log_path=event_log if event_log.parent.exists() else None
        )
        await runtime.start()

        summary = runtime.summary()
        enabled_count = sum(1 for s in summary.values() if s == "enabled")
        click.echo(f"  ✓ {enabled_count}/{len(summary)} plugins enabled\n")

        for name, state in summary.items():
            icon = "✓" if state == "enabled" else "✗"
            click.echo(f"  {icon} {name:<30} [{state}]")

        click.echo(f"\n  Services: {len(runtime.context.list_services())}\n")
        click.echo("Harness is running. Press Ctrl+C to stop.")

        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            click.echo("\n⟳ Shutting down...")
            await runtime.stop()
            click.echo("✓ Harness stopped.")

    try:
        _run_async(_run())
    except KeyboardInterrupt:
        pass


@main.command()
@click.option("--host", default="127.0.0.1", help="Host interface to bind")
@click.option("--port", default=8080, help="Port to listen on")
def ui(host: str, port: int) -> None:
    """Launch the real-time web control room dashboard."""
    import uvicorn

    from harness.commands.agent import FallbackLLM
    from harness.kernel.runtime import HarnessRuntime
    from harness.ui.server import create_app

    runtime = HarnessRuntime.create(db_path=":memory:", fallback_llm=FallbackLLM())
    _run_async(runtime.start())

    app = create_app(runtime)

    click.echo(f"🚀 Harness Web Dashboard launching at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="warning")


@main.group()
def mcp() -> None:
    """Model Context Protocol (MCP) server commands."""


@mcp.command("serve")
def mcp_serve() -> None:
    """Start the MCP STDIO server exposing Harness tools to external agents."""

    async def _serve() -> None:
        from harness.kernel.runtime import HarnessRuntime
        from harness.mcp.server import HarnessMCPServer

        async with HarnessRuntime.create(db_path=":memory:") as runtime:
            tool_reg = runtime.tools
            if not tool_reg:
                raise RuntimeError("Tool registry service not available")
            server = HarnessMCPServer(tool_reg)
            await server.run_stdio()

    _run_async(_serve())


@main.command()
def watch() -> None:
    """Run the harness with live filesystem hot-reloading enabled."""

    async def _watch() -> None:
        from harness.kernel.runtime import HarnessRuntime
        from harness.plugins.watcher import PluginWatcher

        runtime = HarnessRuntime.create(db_path=":memory:")
        await runtime.start()

        watcher = PluginWatcher([Path("plugins")], runtime.loader, runtime.lifecycle)
        watcher.start()

        click.echo("👁️  Harness Watcher active. Monitoring plugins/ for live hot-reload...")
        click.echo("Press Ctrl+C to stop.")

        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            watcher.stop()
            await runtime.stop()
            click.echo("\n✓ Watcher stopped.")

    try:
        _run_async(_watch())
    except KeyboardInterrupt:
        pass


@main.command()
@click.option("-f", "--file", "config_file", required=True, type=click.Path(exists=True), help="Path to declarative config file (.yaml/.json)")
def apply(config_file: str) -> None:
    """Apply and reconcile a declarative configuration tree against Harness."""

    async def _apply() -> None:
        from harness.kernel.runtime import HarnessRuntime

        p = Path(config_file).resolve()
        click.echo(f"🔄 Reconciling configuration from {p.name}...")
        runtime = HarnessRuntime.from_config(p)
        await runtime.start()
        click.echo("✓ Declarative reconciliation applied successfully.")
        await runtime.stop()

    _run_async(_apply())


@main.group()
def config() -> None:
    """Manage and validate declarative configuration trees."""


@config.command("validate")
@click.argument("config_file", type=click.Path(exists=True))
def config_validate(config_file: str) -> None:
    """Validate syntax and schema of a declarative configuration file."""
    import json
    from harness.kernel.reconciler import HarnessConfigTree

    p = Path(config_file).resolve()
    text = p.read_text(encoding="utf-8")
    try:
        try:
            import yaml
            data = yaml.safe_load(text)
        except ImportError:
            data = json.loads(text)
        tree = HarnessConfigTree.model_validate(data)
        click.echo(f"✓ Configuration file {p.name} is valid (version: {tree.version}, plugins: {len(tree.plugins)})")
    except Exception as e:
        click.echo(f"✗ Configuration validation failed: {e}", err=True)
        sys.exit(1)


@main.group()
def skills() -> None:
    """Manage and query the agent skill knowledge graph."""


@skills.command("graph")
@click.option("--visual", is_flag=True, help="Generate interactive HTML visual brief in %TEMP%")
@click.option("--path", default=".", help="Root directory to scan for skills")
def skills_graph(visual: bool, path: str) -> None:
    """Index and display the workspace skill knowledge graph."""
    from harness.commands.skills import export_skill_graph_visual_cmd, index_skills_cmd

    res = index_skills_cmd(path)
    click.echo(f"📊 Indexed {res['indexed_skills']} skills across {len(res['categories'])} categories.")
    click.echo(f"   Nodes: {res['total_nodes']} | Relation Edges: {res['total_edges']}")
    click.echo(f"   Categories: {', '.join(res['categories'])}")

    if visual:
        vis_res = export_skill_graph_visual_cmd()
        click.echo(f"\n🌐 Visual Brief generated: {vis_res['html_path']}")


@skills.command("route")
@click.argument("intent")
@click.option("--top-k", default=3, help="Max matches to return")
def skills_route(intent: str, top_k: int) -> None:
    """Route natural language task intent to matching skills."""
    from harness.commands.skills import route_skills_cmd

    res = route_skills_cmd(intent, top_k=top_k)
    click.echo(f"🎯 Route matches for: {intent!r}")
    for idx, match in enumerate(res["matches"], 1):
        click.echo(f"  {idx}. {match['skill_name']} [{match['category']}] - Confidence: {match['confidence']*100:.1f}%")
        if match["matched_triggers"]:
            click.echo(f"     Triggers: {', '.join(match['matched_triggers'])}")
    if res["recommended_chain"]:
        click.echo(f"\n🔗 Recommended Execution Chain: {' → '.join(res['recommended_chain'])}")


@skills.command("chain")
@click.argument("start_skill")
@click.argument("target_skill")
def skills_chain(start_skill: str, target_skill: str) -> None:
    """Find directed execution path between two skills."""
    from harness.commands.skills import find_skill_chain_cmd

    res = find_skill_chain_cmd(start_skill, target_skill)
    if res["status"] == "ok":
        click.echo(f"🔗 Execution Path ({res['length']} steps):")
        click.echo(f"   {' → '.join(res['chain'])}")
    else:
        click.echo(f"✗ No path found between '{start_skill}' and '{target_skill}'.")


@skills.command("info")
@click.argument("skill_name")
def skills_info(skill_name: str) -> None:
    """Inspect topological dependencies and anti-patterns for a skill."""
    from harness.commands.skills import get_skill_topology_cmd

    res = get_skill_topology_cmd(skill_name)
    if res["status"] == "ok":
        topo = res["topology"]
        skill = topo["skill"]
        click.echo(f"🏷️  Skill: {skill['name']} (v{skill['version']})")
        click.echo(f"   Category: {skill['category']} | Invocation: {skill['invocation']}")
        click.echo(f"   Target: {skill['target'] or skill['description']}")
        if topo["prerequisites"]:
            click.echo(f"   Prerequisites: {', '.join(topo['prerequisites'])}")
        if topo["downstream_handoffs"]:
            click.echo(f"   Downstream Handoffs: {', '.join(topo['downstream_handoffs'])}")
        if topo["mitigated_anti_patterns"]:
            click.echo(f"   Mitigated Anti-Patterns: {', '.join(topo['mitigated_anti_patterns'])}")
    else:
        click.echo(f"✗ {res.get('reason', 'Skill not found')}", err=True)


@skills.command("create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Skill description and trigger bounds")
@click.option("--category", "-c", default="engineering / meta-skills", help="Skill domain category")
@click.option("--target-dir", "-t", default=None, help="Destination directory (defaults to .agents/skills/<name>)")
@click.option("--trigger", "-g", "triggers", multiple=True, help="Trigger phrases for skill routing")
@click.option("--validate", "auto_validate", is_flag=True, help="Validate skill specifications on creation")
def skills_create(
    name: str,
    description: str,
    category: str,
    target_dir: str | None,
    triggers: tuple[str, ...],
    auto_validate: bool,
) -> None:
    """Scaffold a high-precision agent skill with SKILL.md and CARD.md specifications."""
    from harness.commands.skills import scaffold_skill_cmd

    clean_name = name.strip().lower().replace("_", "-")
    result = scaffold_skill_cmd(
        name=clean_name,
        description=description,
        category=category,
        target_dir=target_dir,
        triggers=triggers,
        auto_validate=auto_validate,
    )
    click.echo(f"✨ Scaffolded agent skill '{clean_name}' at: {result.path}")
    for gen in result.generated_files:
        click.echo(f"   📄 {gen.name}")

    if result.validation_report:
        rep = result.validation_report
        status = "✓ VALID" if rep.valid else "✗ INVALID"
        click.echo(f"\n🔍 Pre-Flight Validation: {status}")
        if rep.warnings:
            for w in rep.warnings:
                click.echo(f"   ⚠️  {w}")
        if rep.errors:
            for e in rep.errors:
                click.echo(f"   ❌ {e}")


@skills.command("validate")
@click.argument("skill_dir", default=".")
def skills_validate(skill_dir: str) -> None:
    """Validate an agent skill package against deep-module craft standards."""
    from harness.commands.skills import validate_skill_cmd

    report = validate_skill_cmd(skill_dir)
    target = Path(skill_dir).resolve()
    status = "✓ PASS" if report.valid else "✗ FAIL"
    click.echo(f"Skill Diagnostic Report: {target}")
    click.echo("━" * 58)
    click.echo(f"Overall Status: {status}\n")
    for c in report.checks:
        mark = "  ✓" if c.passed else "  ✗"
        sev = f"[{c.severity.value.upper()}]" if not c.passed else ""
        click.echo(f"{mark} {c.name:<25} {sev} {c.message}")
    if report.warnings:
        click.echo("\nWarnings:")
        for w in report.warnings:
            click.echo(f"  • {w}")
    if report.errors:
        click.echo("\nErrors:")
        for err in report.errors:
            click.echo(f"  • {err}")
    if not report.valid:
        sys.exit(1)


if __name__ == "__main__":
    main()

