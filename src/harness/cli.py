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

# Ensure src is in sys.path when executed directly
_src_dir = Path(__file__).resolve().parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

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
    from harness.commands.workspace import init_workspace_cmd

    res = init_workspace_cmd(path)
    click.echo(f"✓ Workspace initialized at {res.workspace_path}")
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
    from harness.commands.events import get_events_cmd

    log_path = Path(".harness") / "events.jsonl"
    if not log_path.exists():
        click.echo("No event log found. Initialize with 'harness init' first.")
        return

    res = get_events_cmd(event_type=event_type, limit=limit, log_path=log_path)
    if not res.events:
        click.echo("No events found.")
        return

    for evt in res.events:
        ts = evt.timestamp.isoformat()[:19]
        etype = evt.event_type.value
        source = evt.source
        click.echo(f"  {ts}  [{etype}]  {source}")

    click.echo(f"\nShowing {len(res.events)} event(s)")



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
    from harness.commands.creator import scaffold_plugin_cmd

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


creator.add_command(creator_build, name="scaffold")


@creator.command("init")
def creator_init() -> None:
    """Interactive wizard for scaffolding a new plugin project."""
    from harness.commands.creator import scaffold_plugin_cmd

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


@creator.command("validate")
@click.argument("plugin_path", default=".")
@click.option("--dry-run", is_flag=True, default=False, help="Boot sandbox and execute entrypoints")
@click.option("--timeout", default=15.0, help="Sandbox dry-run timeout in seconds")
@click.option("--fix", "--remediate", "remediate", is_flag=True, default=False, help="Automatically repair detected issues")
def creator_validate(plugin_path: str, dry_run: bool, timeout: float, remediate: bool) -> None:
    """Validate a plugin manifest, source files, and sandbox execution."""
    from harness.commands.creator import validate_plugin_cmd

    report = _run_async(validate_plugin_cmd(plugin_path, dry_run=dry_run, timeout=timeout, remediate=remediate))
    click.echo(report.format_cli())
    if not report.valid:
        raise click.ClickException("Validation failed. See details above.")


@creator.command("remediate")
@click.argument("plugin_path", default=".")
def creator_remediate(plugin_path: str) -> None:
    """Auto-repair missing manifest, boilerplate functions, and dependency files."""
    from harness.commands.creator import remediate_plugin_cmd

    report = _run_async(remediate_plugin_cmd(plugin_path))
    click.echo(report.format_cli())
    if report.valid:
        click.echo("✓ Successfully auto-remediated plugin package.")
    else:
        raise click.ClickException("Remediation completed with remaining errors.")


@creator.command("archetypes")
def creator_archetypes() -> None:
    """List all available plugin archetypes and templates."""
    from harness.commands.creator import list_archetypes_cmd

    archetypes = list_archetypes_cmd()
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
        from harness.commands.runtime import run_harness_cmd

        event_log = Path(".harness") / "events.jsonl"
        click.echo("⟳ Loading built-in and ecosystem plugins...")

        res = await run_harness_cmd(
            event_log_path=event_log if event_log.parent.exists() else None,
            blocking=False,
        )
        runtime = res.runtime
        click.echo(f"  ✓ {res.enabled_count}/{len(res.summary)} plugins enabled\n")

        for name, state in res.summary.items():
            icon = "✓" if state == "enabled" else "✗"
            click.echo(f"  {icon} {name:<30} [{state}]")

        click.echo(f"\n  Services: {res.services_count}\n")
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
    from harness.commands.mcp import serve_mcp_cmd

    _run_async(serve_mcp_cmd(stdio=True))


@main.command()
def watch() -> None:
    """Run the harness with live filesystem hot-reloading enabled."""

    async def _watch() -> None:
        from harness.commands.workspace import watch_workspace_cmd
        from harness.kernel.runtime import HarnessRuntime

        runtime = HarnessRuntime.create(db_path=":memory:")
        await runtime.start()

        watcher = await watch_workspace_cmd(
            plugin_dirs=[Path("plugins")],
            runtime=runtime,
        )

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
        from harness.commands.runtime import apply_config_cmd

        p = Path(config_file).resolve()
        click.echo(f"🔄 Reconciling configuration from {p.name}...")
        await apply_config_cmd(p)
        click.echo("✓ Declarative reconciliation applied successfully.")

    _run_async(_apply())


@main.group()
def config() -> None:
    """Manage and validate declarative configuration trees."""


@config.command("validate")
@click.argument("config_file", type=click.Path(exists=True))
def config_validate(config_file: str) -> None:
    """Validate syntax and schema of a declarative configuration file."""
    from harness.commands.runtime import validate_config_cmd

    p = Path(config_file).resolve()
    res = validate_config_cmd(p)
    if res.valid:
        click.echo(f"✓ Configuration file {p.name} is valid (version: {res.version}, plugins: {res.plugins_count})")
    else:
        click.echo(f"✗ Configuration validation failed: {res.error_message}", err=True)
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
        for err in report.errors:
            click.echo(f"  • {err}")
    if not report.valid:
        sys.exit(1)


@main.command("assess-compute")
@click.argument("prompt")
@click.option("--files", "-f", "files_count", default=1, type=int, help="Number of files in target task scope")
@click.option("--arch", "-a", "is_architecture", is_flag=True, help="Mark task as architectural refactoring")
@click.option("--debug-task", "-d", "is_debugging", is_flag=True, help="Mark task as debugging / diagnostic investigation")
@click.option("--profile", "-p", "profile", type=click.Choice(["balanced", "reasoning_heavy", "cost_optimized", "latency_optimized"]), default="balanced", help="Scoring profile heuristic preset")
@click.option("--override", "-o", "override_tier", type=click.Choice(["high_reasoning", "standard_agentic", "fast_mechanical", "high", "medium", "low"]), default=None, help="Force specific model tier override")
@click.option("--json", "output_json", is_flag=True, help="Output raw assessment in JSON format")
@click.option("--html", "generate_html", is_flag=True, help="Generate interactive HTML visual review brief in %TEMP%")
def assess_compute(
    prompt: str,
    files_count: int,
    is_architecture: bool,
    is_debugging: bool,
    profile: str,
    override_tier: str | None,
    output_json: bool,
    generate_html: bool,
) -> None:
    """Assess task surface complexity and recommend optimal model tier & reasoning budget."""
    from harness.commands.compute import assess_compute_cmd

    res = assess_compute_cmd(
        prompt,
        files_count=files_count,
        is_architecture=is_architecture,
        is_debugging=is_debugging,
        override_tier=override_tier,
        profile=profile,
        generate_html=generate_html,
        task_title="CLI Compute Assessment",
    )

    if output_json:
        click.echo(json.dumps(res.assessment.to_dict(), indent=2))
        return

    click.echo("\n" + res.recommendation_block)


@main.group("bridge")
def bridge_cmd() -> None:
    """Check and inspect peer ecosystem bridges."""
    pass


@bridge_cmd.command("list")
def bridge_list() -> None:
    """List all registered ecosystem bridges and their availability."""
    from harness.commands.bridges import list_bridges_cmd

    bridges = list_bridges_cmd()
    click.echo(f"\nEcosystem Bridges ({len(bridges)} registered):\n" + "━" * 70)
    for b in bridges:
        mark = "✓" if b["available"] else "✗"
        path_str = b["path"] or f"Missing (set {b['env_var']})"
        click.echo(f"  {mark} {b['project_name']:<18} [{b['status']}]")
        click.echo(f"      Path: {path_str}")
        if b["capabilities"]:
            click.echo(f"      Capabilities: {', '.join(b['capabilities'])}")
    click.echo()


@bridge_cmd.command("status")
@click.argument("name", required=False, default=None)
def bridge_status(name: str | None) -> None:
    """Inspect detailed diagnostic health of ecosystem bridges."""
    from harness.commands.bridges import check_bridge_status_cmd

    res = check_bridge_status_cmd(project_name=name)
    if "bridge" in res:
        b = res["bridge"]
        status_sym = "✓ CONNECTED" if b["available"] else "✗ NOT FOUND"
        click.echo(f"\nBridge Diagnostic Report: {b['project_name']}")
        click.echo("━" * 58)
        click.echo(f"Status:       {status_sym} ({b['status']})")
        click.echo(f"Substrate:    {b['path'] or 'None'}")
        click.echo(f"Env Variable: {b['env_var']}")
        click.echo(f"Capabilities: {', '.join(b['capabilities']) if b['capabilities'] else 'None'}\n")
    else:
        click.echo(f"\nEcosystem Bridges Overview: {res['connected_bridges']}/{res['total_bridges']} Connected")
        click.echo("━" * 58)
        for b in res["bridges"]:
            mark = "✓" if b["available"] else "✗"
            click.echo(f"  {mark} {b['project_name']:<16} [{b['status']}] -> {b['path'] or 'missing'}")
        click.echo()


@main.group("knowledge")
def knowledge_cmd() -> None:
    """Manage and query the distilled Knowledge Vault and Isnad lineage."""
    pass


@knowledge_cmd.command("sync")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option("--db", "db_path", default=None, help="Path to SQLite storage database (defaults to ~/.harness/storage.db)")
def knowledge_sync(vault_dir: str, db_path: str | None) -> None:
    """Sync all on-disk Knowledge Items from .harness/knowledge/ into the storage database."""
    from harness.services.storage import SQLiteStorageService

    storage_path = db_path or (Path.home() / ".harness" / "storage.db")
    storage = SQLiteStorageService(storage_path)

    async def _sync():
        count = await storage.sync_knowledge_vault(vault_dir)
        return count

    synced = _run_async(_sync())
    storage.close()
    click.echo(f"✓ Successfully synced {synced} Knowledge Item(s) from '{vault_dir}' into storage.")


@knowledge_cmd.command("list")
@click.option("--tag", "-t", default=None, help="Filter by tag")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
def knowledge_list(tag: str | None, vault_dir: str) -> None:
    """List all Knowledge Items in storage (hydrates from disk if DB is empty)."""
    from harness.services.storage import SQLiteStorageService

    storage = SQLiteStorageService(":memory:")

    async def _list():
        await storage.sync_knowledge_vault(vault_dir)
        return await storage.list_knowledge_items(tag=tag)

    items = _run_async(_list())
    storage.close()

    click.echo(f"\nKnowledge Vault ({len(items)} items):\n" + "━" * 70)
    for item in items:
        tags_str = f"[{', '.join(item.tags)}]" if item.tags else ""
        click.echo(f"  • {item.id:<20} {item.title:<40} {tags_str}")
    click.echo()


@knowledge_cmd.command("query")
@click.argument("query_str")
@click.option("--tag", "-t", default=None, help="Filter by tag")
@click.option("--status", "-s", default=None, help="Filter by Isnad status (e.g. VERIFIED)")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
def knowledge_query(query_str: str, tag: str | None, status: str | None, vault_dir: str) -> None:
    """Search Knowledge Items by keyword, tag, or Isnad status."""
    from harness.services.storage import SQLiteStorageService

    storage = SQLiteStorageService(":memory:")

    async def _query():
        await storage.sync_knowledge_vault(vault_dir)
        return await storage.query_knowledge(query=query_str, tag=tag, status=status)

    results = _run_async(_query())
    storage.close()

    click.echo(f"\nQuery Results for '{query_str}' ({len(results)} matches):\n" + "━" * 70)
    for item in results:
        status_val = (
            item.isnad.status
            if hasattr(item.isnad, "status")
            else item.isnad.get("status", "UNKNOWN")
            if isinstance(item.isnad, dict)
            else "UNKNOWN"
        )
        click.echo(f"  [{status_val}] {item.id}: {item.title}")
        if item.summary:
            summary_first = item.summary.split("\n")[0].strip("# ")
            click.echo(f"      {summary_first[:80]}")
    click.echo()


@knowledge_cmd.command("verify")
@click.argument("ki_id")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
def knowledge_verify(ki_id: str, vault_dir: str) -> None:
    """Audit Isnad lineage nodes and primary source file existence for a Knowledge Item."""
    from harness.services.storage import SQLiteStorageService

    storage = SQLiteStorageService(":memory:")

    async def _verify():
        await storage.sync_knowledge_vault(vault_dir)
        return await storage.verify_isnad_integrity(ki_id)

    report = _run_async(_verify())
    storage.close()

    if report.get("status") == "error":
        click.echo(f"✗ Error: {report.get('error')}")
        sys.exit(1)

    status_symbol = "✓ PASS" if report.get("integrity_verified") else "⚠ WARNING (Some lineage targets missing)"
    click.echo(f"\nIsnad Lineage Audit: {report.get('ki_id')} — {report.get('title')}")
    click.echo("━" * 70)
    click.echo(f"Integrity Status: {status_symbol}")
    click.echo(f"Isnad Claim Status: {report.get('isnad_status')}\n")

    for claim in report.get("claims_audited", []):
        click.echo(f"Claim: \"{claim.get('assertion')}\"")
        for node in claim.get("nodes", []):
            mark = "  ✓" if node.get("file_exists") else "  ✗"
            click.echo(f"  {mark} {node.get('uri')} -> exists: {node.get('file_exists')}")
    click.echo()


if __name__ == "__main__":
    main()


