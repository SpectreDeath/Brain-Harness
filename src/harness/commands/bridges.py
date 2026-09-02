"""Ecosystem Bridge commands — pure async and synchronous entry points for bridge diagnostics."""

from __future__ import annotations

from typing import Any
from harness.bridges.locator import EcosystemLocator


def list_bridges_cmd() -> list[dict[str, Any]]:
    """Return discovery and capability status for all registered ecosystem bridges."""
    reports = EcosystemLocator.inspect_all()
    return [r.model_dump() for r in reports]


def check_bridge_status_cmd(project_name: str | None = None) -> dict[str, Any]:
    """Inspect status of a specific bridge or all bridges."""
    if project_name:
        report = EcosystemLocator.inspect_bridge(project_name)
        return {
            "status": "ok",
            "bridge": report.model_dump(),
        }

    reports = EcosystemLocator.inspect_all()
    connected_count = sum(1 for r in reports if r.available)
    return {
        "status": "ok",
        "total_bridges": len(reports),
        "connected_bridges": connected_count,
        "bridges": [r.model_dump() for r in reports],
    }


# --- Click CLI adapters ---
import click


@click.group("bridge")
def bridge_group() -> None:
    """Inspect and manage ecosystem bridges (Em-Cubed, Memtext, Skill Flywheel)."""


@bridge_group.command("list")
def bridge_list() -> None:
    """List all registered ecosystem bridges and their availability."""
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


@bridge_group.command("status")
@click.argument("name", required=False, default=None)
def bridge_status(name: str | None) -> None:
    """Check discovery status of peer ecosystem repositories."""
    if name:
        res = check_bridge_status_cmd(project_name=name)
        b = res["bridge"]
        status_sym = "✓ CONNECTED" if b["available"] else "✗ NOT FOUND"
        click.echo(f"\nBridge Diagnostic Report: {b['project_name']}")
        click.echo("━" * 58)
        click.echo(f"Status:       {status_sym} ({b['status']})")
        click.echo(f"Substrate:    {b['path'] or 'None'}")
        click.echo(f"Env Variable: {b['env_var']}")
        click.echo(f"Capabilities: {', '.join(b['capabilities']) if b['capabilities'] else 'None'}\n")
    else:
        status_map = EcosystemLocator.status()
        click.echo("\nEcosystem Bridges Overview")
        click.echo(f"{'Ecosystem Component':<20} {'Status':<15} {'Override Env Var':<22} {'Path'}")
        click.echo("─" * 85)

        for pname, info in status_map.items():
            st = "✓ Available" if info["available"] else "✗ Not found"
            p = info["path"] or "(not discovered)"
            click.echo(f"{pname:<20} {st:<15} {info['env_var']:<22} {p}")


__all__ = [
    "bridge_group",
    "check_bridge_status_cmd",
    "list_bridges_cmd",
]
