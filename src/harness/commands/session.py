"""Session commands — pure async command handlers for agent execution session state.

Allows headless query, inspection, hierarchical tree visualization, and export
of persistent agent execution trajectories across CLI, MCP, Web UI, and Swarm engines.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from harness.agent.session import (
    AGENT_SESSION_MANAGER_KEY,
    AgentSessionManager,
    AgentSessionPlugin,
)
from harness.kernel.context import ServiceContext
from harness.services.storage import StoragePlugin

logger = structlog.get_logger()


@dataclass
class SessionListResult:
    """Result of listing execution sessions."""

    total_count: int
    sessions: list[dict[str, Any]]
    root_only: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_count": self.total_count,
            "sessions": self.sessions,
            "root_only": self.root_only,
        }


@dataclass
class SessionDetailResult:
    """Result of retrieving a single session."""

    found: bool
    session_id: str
    session: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "found": self.found,
            "session_id": self.session_id,
            "session": self.session,
        }


@dataclass
class SessionTreeResult:
    """Result of retrieving a hierarchical session execution tree."""

    found: bool
    session_id: str
    tree: dict[str, Any] | None = None
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "found": self.found,
            "session_id": self.session_id,
            "tree": self.tree,
            "metrics": self.metrics,
        }


@dataclass
class SessionExportResult:
    """Result of exporting an agent session trajectory."""

    session_id: str
    format: str
    content: str
    written_file: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "format": self.format,
            "content": self.content,
            "written_file": self.written_file,
        }


@dataclass
class SessionDeleteResult:
    """Result of deleting a session."""

    session_id: str
    deleted: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "deleted": self.deleted,
        }


async def _get_or_create_session_manager(
    context: ServiceContext | None = None,
) -> AgentSessionManager:
    """Retrieve or initialize the active AgentSessionManager."""
    if context is not None and hasattr(context, "has") and context.has(AGENT_SESSION_MANAGER_KEY):
        return context.require(AGENT_SESSION_MANAGER_KEY)

    # Initialize a lightweight stand-alone manager
    ctx = context or ServiceContext()
    if not ctx.has(AGENT_SESSION_MANAGER_KEY):
        # Auto-enable storage if available
        storage_plugin = StoragePlugin()
        await storage_plugin.on_load(ctx)
        await storage_plugin.on_enable()

        sess_plugin = AgentSessionPlugin()
        await sess_plugin.on_load(ctx)
        await sess_plugin.on_enable()

    return ctx.require(AGENT_SESSION_MANAGER_KEY)


async def list_sessions_cmd(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    root_only: bool = False,
    context: ServiceContext | None = None,
) -> SessionListResult:
    """List agent execution sessions."""
    manager = await _get_or_create_session_manager(context)
    if root_only:
        sessions = await manager.list_root_sessions(status=status, limit=limit, offset=offset)
    else:
        sessions = await manager.list_sessions(status=status, limit=limit, offset=offset)

    dicts = [s.to_dict() for s in sessions]
    return SessionListResult(
        total_count=len(dicts),
        sessions=dicts,
        root_only=root_only,
    )


async def get_session_cmd(
    session_id: str,
    context: ServiceContext | None = None,
) -> SessionDetailResult:
    """Get details of a single agent session."""
    manager = await _get_or_create_session_manager(context)
    sess = await manager.get_session(session_id)
    if not sess:
        return SessionDetailResult(found=False, session_id=session_id, session=None)
    return SessionDetailResult(found=True, session_id=session_id, session=sess.to_dict())


async def get_session_tree_cmd(
    session_id: str,
    context: ServiceContext | None = None,
) -> SessionTreeResult:
    """Retrieve hierarchical session tree with recursive rollups."""
    manager = await _get_or_create_session_manager(context)
    tree = await manager.get_session_tree(session_id)
    if not tree:
        return SessionTreeResult(found=False, session_id=session_id, tree=None, metrics={})

    metrics = await manager.get_subtree_metrics(session_id)
    return SessionTreeResult(found=True, session_id=session_id, tree=tree, metrics=metrics)


async def export_session_cmd(
    session_id: str,
    format: str = "json",
    output_file: str | Path | None = None,
    context: ServiceContext | None = None,
) -> SessionExportResult:
    """Export session trajectory to JSON or Markdown."""
    manager = await _get_or_create_session_manager(context)
    content = await manager.export_session(session_id, format=format)
    written: str | None = None
    if output_file:
        out_path = Path(output_file).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        written = str(out_path)

    return SessionExportResult(
        session_id=session_id,
        format=format,
        content=content,
        written_file=written,
    )


async def delete_session_cmd(
    session_id: str,
    context: ServiceContext | None = None,
) -> SessionDeleteResult:
    """Delete an agent execution session."""
    manager = await _get_or_create_session_manager(context)
    deleted = await manager.store.delete(session_id)
    return SessionDeleteResult(session_id=session_id, deleted=deleted)


# --- Click CLI adapters ---
import json
import click
from harness.commands._utils import _run_async


@click.group("session")
def session_group() -> None:
    """Manage and inspect agent execution sessions and hierarchical trees."""


@session_group.command("list")
@click.option("--status", "-s", default=None, help="Filter by session status")
@click.option("--limit", "-n", default=20, type=int, help="Limit number of sessions")
@click.option("--root-only", is_flag=True, help="List only root-level sessions")
def session_list(status: str | None, limit: int, root_only: bool) -> None:
    """List agent execution sessions."""
    res = _run_async(list_sessions_cmd(status=status, limit=limit, root_only=root_only))
    click.echo(f"\nFound {res.total_count} session(s):")
    click.echo("─" * 75)
    for s in res.sessions:
        click.echo(f"• ID: {s['session_id']} | Status: {s['status']} | Steps: {len(s.get('steps', []))} | Task: {s['task'][:40]}")
    click.echo()


@session_group.command("get")
@click.argument("session_id")
def session_get(session_id: str) -> None:
    """Get details of a specific agent session."""
    res = _run_async(get_session_cmd(session_id))
    if not res.found or not res.session:
        click.echo(f"Error: Session '{session_id}' not found", err=True)
        return
    click.echo(json.dumps(res.session, indent=2))


@session_group.command("tree")
@click.argument("session_id")
def session_tree(session_id: str) -> None:
    """Show hierarchical session execution tree and rollups."""
    res = _run_async(get_session_tree_cmd(session_id))
    if not res.found or not res.tree:
        click.echo(f"Error: Session '{session_id}' not found", err=True)
        return

    metrics = res.metrics
    click.echo(f"\nExecution Tree for Session: {session_id}")
    click.echo("━" * 60)
    click.echo(f"Total Subtree Sessions: {metrics.get('total_sessions', 1)}")
    click.echo(f"Total Tokens:           {metrics.get('total_tokens', 0)}")
    click.echo(f"Total Steps:            {metrics.get('total_steps', 0)}")
    click.echo(f"Completed / Failed:     {metrics.get('completed_count', 0)} / {metrics.get('failed_count', 0)}")
    click.echo(f"Duration:               {metrics.get('total_duration', 0.0):.2f}s")
    click.echo("\nTree Hierarchy:")
    click.echo("─" * 60)

    def _print_node(node: dict[str, Any], indent: int = 0) -> None:
        prefix = "  " * indent + "└─ " if indent > 0 else "• "
        sid = node.get("session_id", "")
        role = node.get("role") or "agent"
        status = node.get("status", "")
        task = (node.get("task") or "")[:40]
        click.echo(f"{prefix}[{role}] {sid} ({status}) — {task}")
        for child in node.get("children", []):
            _print_node(child, indent + 1)

    _print_node(res.tree)
    click.echo()


@session_group.command("export")
@click.argument("session_id")
@click.option("--format", "-f", "fmt", default="markdown", type=click.Choice(["markdown", "json", "md"], case_sensitive=False))
@click.option("--output", "-o", "out_file", default=None, help="Output file path")
def session_export(session_id: str, fmt: str, out_file: str | None) -> None:
    """Export agent session trajectory to Markdown or JSON."""
    res = _run_async(export_session_cmd(session_id, format=fmt, output_file=out_file))
    if out_file:
        click.echo(f"✓ Exported session trajectory to: {res.written_file}")
    else:
        click.echo(res.content)


__all__ = [
    "SessionDeleteResult",
    "SessionDetailResult",
    "SessionExportResult",
    "SessionListResult",
    "SessionTreeResult",
    "delete_session_cmd",
    "export_session_cmd",
    "get_session_cmd",
    "get_session_tree_cmd",
    "list_sessions_cmd",
    "session_group",
]
