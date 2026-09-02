"""System commands — pure async entry points for runtime introspection."""

from __future__ import annotations

from typing import Any


async def list_services(db_path: str = ":memory:") -> dict[str, str | None]:
    """Return a mapping of service key names to provider plugin names.

    Args:
        db_path: SQLite database path for the runtime (default in-memory).
    """
    from harness.kernel.runtime import HarnessRuntime

    async with HarnessRuntime.create(db_path=db_path, auto_load_user_plugins=False) as runtime:
        return runtime.context.list_services()


async def run_introspect(db_path: str = ":memory:") -> dict[str, Any]:
    """Return a full status snapshot of the running system.

    Returns a dict with ``plugins``, ``services``, ``tools``, and the
    Mermaid graph string — ready for display or JSON serialisation.
    """
    from harness.creator.introspection import RuntimeIntrospector
    from harness.kernel.runtime import HarnessRuntime

    async with HarnessRuntime.create(
        db_path=db_path,
        auto_load_user_plugins=True,
        lazy_external_plugins=True,
    ) as runtime:
        introspector = RuntimeIntrospector(
            runtime.context,
            runtime.lifecycle,
            runtime.tools,
        )
        report = introspector.get_status_report()
        graph = introspector.generate_mermaid_graph()
        return {**report, "graph": graph}


# --- Click CLI adapters ---
import click
from harness.commands._utils import _run_async


@click.command("services")
def services_cli() -> None:
    """List registered services and their provider plugins."""
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


@click.command("introspect")
def introspect_cli() -> None:
    """Display runtime system diagnostics and dependency graph."""
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


__all__ = [
    "introspect_cli",
    "list_services",
    "run_introspect",
    "services_cli",
]

