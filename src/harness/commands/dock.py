"""Dock commands — headless CLI and IoC service seams for Agent Dock workstation ports."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Any

import click
import structlog

from harness.commands._utils import _run_async
from harness.services.dock import (
    DockApprovalDriftError,
    DockBoundaryViolationError,
    DockError,
    DockManifest,
    DockPermissionError,
    DockProcedureCycleError,
    resolve_dock_service,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logger = structlog.get_logger(__name__)


def _manifest_to_dict(manifest: DockManifest) -> dict[str, Any]:
    return {
        "name": manifest.name,
        "description": manifest.description,
        "declared": manifest.declared,
        "manifest_path": manifest.manifest_path,
        "sha256": manifest.sha256,
        "permissions": asdict(manifest.permissions),
        "boundaries": asdict(manifest.boundaries),
        "tools": list(manifest.tools),
        "entrypoints": {
            name: {
                "name": proc.name,
                "description": proc.description,
                "write_path": proc.write_path,
                "steps": [asdict(s) for s in proc.steps],
            }
            for name, proc in manifest.entrypoints.items()
        },
        "warnings": list(manifest.warnings),
    }


@click.group("dock")
def dock_group() -> None:
    """Agent Dock — workstation port for plugging agents into repositories."""


@dock_group.command("inspect")
@click.argument("repo_or_path", default=".", required=False)
@click.option("--json", "as_json", is_flag=True, help="Output inspection report as JSON")
def dock_inspect(repo_or_path: str, as_json: bool) -> None:
    """Inspect repository dock manifest without linking or state changes."""
    service = resolve_dock_service()
    try:
        manifest = service.inspect(repo_or_path)
    except Exception as e:
        raise click.ClickException(str(e)) from e

    data = _manifest_to_dict(manifest)
    if as_json:
        click.echo(json.dumps(data, indent=2))
        return

    dock_type = "Declared (dock.yaml)" if manifest.declared else "Generic Fallback"
    click.echo(f"\n⚓ Agent Dock: {manifest.name}")
    click.echo(f"  Type:        {dock_type}")
    click.echo(f"  Description: {manifest.description}")
    if manifest.manifest_path:
        click.echo(f"  Manifest:    {manifest.manifest_path}")
        click.echo(f"  SHA-256:     {manifest.sha256}")

    click.echo("\n  Permissions:")
    click.echo(f"    read:  {'✓' if manifest.permissions.read else '✗'}")
    click.echo(f"    run:   {'✓' if manifest.permissions.run else '✗'}")
    click.echo(f"    write: {'✓' if manifest.permissions.write else '✗'}")
    click.echo(f"    push:  {'✓' if manifest.permissions.push else '✗'}")

    click.echo("\n  Boundaries:")
    click.echo(f"    Paths:      {', '.join(manifest.boundaries.paths) or 'none'}")
    click.echo(f"    Operations: {', '.join(manifest.boundaries.operations) or 'none'}")

    click.echo("\n  Declared Procedures:")
    if not manifest.entrypoints:
        click.echo("    (none)")
    else:
        for name, proc in manifest.entrypoints.items():
            write_marker = " [write-path]" if proc.write_path else ""
            click.echo(f"    • {name}{write_marker}: {proc.description or 'No description'}")
            for s_idx, s in enumerate(proc.steps, start=1):
                if s.call_procedure:
                    click.echo(f"        step {s_idx}: call -> {s.call_procedure}")
                else:
                    click.echo(f"        step {s_idx}: {s.command} (in '{s.workdir}')")

    click.echo("\n  Exposed Tools:")
    if not manifest.tools:
        click.echo("    (none)")
    else:
        for tool in manifest.tools:
            click.echo(f"    • {tool}")

    if manifest.warnings:
        click.echo("\n  ⚠️  Warnings:")
        for w in manifest.warnings:
            click.echo(f"    - {w}")
    click.echo("")


@dock_group.command("link")
@click.argument("repo_or_path")
@click.option("--name", default=None, help="Custom alias for the linked dock")
@click.option("--approve", is_flag=True, help="Approve declared permissions and boundaries")
@click.option("--json", "as_json", is_flag=True, help="Output link record as JSON")
def dock_link(repo_or_path: str, name: str | None, approve: bool, as_json: bool) -> None:
    """Link an agent dock and record its approval digest."""
    service = resolve_dock_service()
    try:
        manifest = service.inspect(repo_or_path)
    except Exception as e:
        raise click.ClickException(f"Failed to inspect repository: {e}") from e

    approved = approve
    if not approved:
        if sys.stdin.isatty():
            click.echo(f"\n⚓ Discovered Agent Dock '{name or manifest.name}'")
            click.echo(f"   Declared:    {manifest.declared}")
            click.echo(f"   SHA-256:     {manifest.sha256 or '(generic)'}")
            click.echo(f"   Permissions: read={manifest.permissions.read}, run={manifest.permissions.run}, write={manifest.permissions.write}, push={manifest.permissions.push}")
            click.echo(f"   Boundaries:  {len(manifest.boundaries.paths)} paths, {len(manifest.boundaries.operations)} operations")
            click.echo(f"   Procedures:  {len(manifest.entrypoints)}")
            click.echo("")
            approved = click.confirm("Approve docking with these permissions and boundaries?", default=False)
        else:
            approved = False

    try:
        record = service.link(repo_or_path, name=name, approve=approved)
    except Exception as e:
        raise click.ClickException(f"Failed to link dock: {e}") from e

    data = asdict(record)
    if as_json:
        click.echo(json.dumps(data, indent=2))
        return

    status_str = "APPROVED" if record.approved else "UNAPPROVED"
    click.echo(f"\n✓ Linked dock '{record.dock_name}' [{status_str}]")
    click.echo(f"  Repo path:    {record.repo_path}")
    click.echo(f"  Transport:    {record.transport}")
    click.echo(f"  Declared:     {record.declared}")
    if record.approved:
        click.echo(f"  Approved SHA: {record.approved_sha256[:12] if record.approved_sha256 else '(generic)'}")
    else:
        click.echo("  Note: Run with '--approve' or confirm interactively to execute procedures.")
    click.echo("")


@dock_group.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output dock list as JSON")
def dock_list(as_json: bool) -> None:
    """List all linked agent docks and their approval status."""
    service = resolve_dock_service()
    docks = service.list_docks()

    if as_json:
        click.echo(json.dumps(docks, indent=2))
        return

    if not docks:
        click.echo("No linked docks found. Run 'harness dock link <repo>' to link one.")
        return

    click.echo(f"\n{'DOCK NAME':<20} {'STATUS':<18} {'DECLARED':<10} {'REPO PATH'}")
    click.echo("-" * 75)
    for d in docks:
        click.echo(
            f"{d['dock_name']:<20} {d['status']:<18} {str(d['declared']):<10} {d['repo_path']}"
        )
    click.echo("")


@dock_group.command("tools")
@click.argument("dock_name")
@click.option("--json", "as_json", is_flag=True, help="Output tools list as JSON")
def dock_tools(dock_name: str, as_json: bool) -> None:
    """List tools exposed by a linked dock."""
    service = resolve_dock_service()
    try:
        tools = service.tools(dock_name)
    except Exception as e:
        raise click.ClickException(str(e)) from e

    if as_json:
        click.echo(json.dumps({"dock_name": dock_name, "tools": tools}, indent=2))
        return

    click.echo(f"\n⚓ Tools exposed by dock '{dock_name}':")
    if not tools:
        click.echo("  (no tools declared)")
    else:
        for t in tools:
            click.echo(f"  • {t}")
    click.echo("")


@dock_group.command("run")
@click.argument("dock_name")
@click.argument("procedure_name")
@click.option("--dry-run", is_flag=True, help="Simulate execution without running commands")
@click.option("--json", "as_json", is_flag=True, help="Output run results as JSON")
def dock_run(dock_name: str, procedure_name: str, dry_run: bool, as_json: bool) -> None:
    """Execute a declared procedure on a linked agent dock."""
    service = resolve_dock_service()

    try:
        result = service.run(dock_name, procedure_name, dry_run=dry_run)
    except DockApprovalDriftError as e:
        raise click.ClickException(f"Approval drift error: {e}") from e
    except DockBoundaryViolationError as e:
        raise click.ClickException(f"Boundary violation: {e}") from e
    except DockPermissionError as e:
        raise click.ClickException(f"Permission denied: {e}") from e
    except DockProcedureCycleError as e:
        raise click.ClickException(f"Procedure cycle: {e}") from e
    except Exception as e:
        raise click.ClickException(str(e)) from e

    data = asdict(result)
    if as_json:
        click.echo(json.dumps(data, indent=2))
        if not result.success:
            sys.exit(1)
        return

    mode_str = "[DRY-RUN] " if dry_run else ""
    click.echo(f"\n⚓ {mode_str}Running '{procedure_name}' on dock '{dock_name}'...")

    for step in result.steps:
        status_icon = "✓" if step.success else "✗"
        called_note = f" (via {step.called_procedure})" if step.called_procedure else ""
        click.echo(f"  {status_icon} Step {step.step_index}{called_note}: {step.command} [{step.duration_seconds:.2f}s]")
        if step.stdout and not dry_run:
            for line in step.stdout.strip().splitlines()[:15]:
                click.echo(f"      {line}")
            if len(step.stdout.strip().splitlines()) > 15:
                click.echo("      ...")
        if not step.success and step.stderr:
            click.echo(f"      [stderr]: {step.stderr.strip()[:300]}")

    if result.success:
        click.echo(f"\n✓ Procedure '{procedure_name}' completed successfully in {result.total_duration_seconds:.2f}s.\n")
    else:
        click.echo(f"\n✗ Procedure '{procedure_name}' failed at step {result.failed_step_index}: {result.error}\n")
        sys.exit(1)


__all__ = [
    "dock_group",
    "dock_inspect",
    "dock_link",
    "dock_list",
    "dock_run",
    "dock_tools",
]

