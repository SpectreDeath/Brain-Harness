"""Headless Click CLI commands for Pi-Style Coding Agent Harness (Tau).

Rule 6: Single-source co-located Click group declaration.
Rule 10: Headless CLI inspection and export seams.
Rule 23: Windows UTF-8 stream codec entrypoint invariant.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click
import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.kernel.context import ServiceContext
from harness.services.tau_bridge import (
    TAU_HARNESS_BRIDGE_SERVICE_KEY,
    DefaultTauHarnessBridgeService,
    ProjectTrustEvaluator,
    SessionJournalManager,
    SessionNode,
    SessionTreeResolver,
    TauBridgeService,
    ToolHistoryRepairEngine,
)

logger = structlog.get_logger(__name__)


def get_tau_service(context: ServiceContext | None = None) -> TauBridgeService:
    """Retrieve or bootstrap the TauBridgeService singleton."""
    if context is not None:
        svc = context.optional(TAU_HARNESS_BRIDGE_SERVICE_KEY)
        if svc is not None:
            return svc

    try:
        from plugins.agent_orchestration.tau_harness_bridge.main import (
            plugin as tau_plugin,
        )

        return tau_plugin
    except Exception as exc:
        logger.debug("tau_plugin_fallback_failed", error=str(exc))
        return DefaultTauHarnessBridgeService()


# ---------------------------------------------------------------------------
# Pure Command Functions (Callable without Click)
# ---------------------------------------------------------------------------


def render_session_tree_cmd(
    journal_path: str | Path,
    root_id: str | None = None,
) -> str:
    """Load session entries from journal and return deterministic ASCII tree."""
    entries = SessionJournalManager.load_entries(journal_path)
    return SessionTreeResolver.render_ascii_tree(entries, root_id=root_id)


def resolve_session_path_cmd(
    journal_path: str | Path,
    target_id: str,
) -> dict[str, Any]:
    """Resolve linear conversation ancestry to target_id from a session journal."""
    entries = SessionJournalManager.load_entries(journal_path)
    path = SessionTreeResolver.resolve_path(entries, target_id)
    return {
        "target_id": path.target_id,
        "depth": path.depth,
        "total_entries": path.total_entries,
        "branch_count": path.branch_count,
        "path": [node.to_dict() for node in path.path_entries],
    }


def repair_tool_history_cmd(
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Execute tool history normalization and return report dict."""
    res = ToolHistoryRepairEngine.repair(messages)
    return {
        "is_modified": res.is_modified,
        "dropped_count": res.dropped_count,
        "synthesized_count": res.synthesized_count,
        "repairs_applied": list(res.repairs_applied),
        "repaired_messages": [dict(m) for m in res.repaired_messages],
    }


def evaluate_project_trust_cmd(
    project_path: str,
    trusted_roots: list[str] | None = None,
) -> dict[str, Any]:
    """Evaluate workspace trust and return diagnostic dict."""
    res = ProjectTrustEvaluator.evaluate(project_path, trusted_roots)
    return {
        "project_path": res.project_path,
        "is_trusted": res.is_trusted,
        "git_root": res.git_root,
        "permission_level": res.permission_level,
        "protected_assets": list(res.protected_assets),
        "warnings": list(res.warnings),
    }


def append_journal_entry_cmd(
    journal_path: str | Path,
    node_id: str,
    parent_id: str | None = None,
    role: str = "user",
    content: str = "",
) -> dict[str, Any]:
    """Append a new node to the locked session journal."""
    node = SessionNode(
        id=node_id,
        parent_id=parent_id,
        role=role,
        content=content,
    )
    saved = SessionJournalManager.append_entry(journal_path, node)
    return saved.to_dict()


# ---------------------------------------------------------------------------
# Click CLI Seam (Rule 6 & Rule 10)
# ---------------------------------------------------------------------------


@click.group("tau")
def tau_group() -> None:
    """Pi-style coding agent harness commands (DAG trees, journals, repair, trust)."""


@tau_group.command("tree")
@click.option(
    "--file",
    "-f",
    "journal_file",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to the JSONL session journal.",
)
@click.option(
    "--root",
    "-r",
    "root_id",
    default=None,
    help="Optional root entry ID to start traversal.",
)
def tau_tree(journal_file: str, root_id: str | None) -> None:
    """Render deterministic ASCII DAG tree of a session journal."""
    tree_str = render_session_tree_cmd(journal_file, root_id=root_id)
    click.echo(tree_str)


@tau_group.command("resolve-path")
@click.option(
    "--file",
    "-f",
    "journal_file",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to the JSONL session journal.",
)
@click.option(
    "--target",
    "-t",
    "target_id",
    required=True,
    help="Target session entry ID to trace back to root.",
)
def tau_resolve_path(journal_file: str, target_id: str) -> None:
    """Resolve linear conversation ancestry from root to target entry."""
    try:
        res = resolve_session_path_cmd(journal_file, target_id)
        click.echo(f"Resolved Ancestry to Target [{target_id}]:")
        click.echo(f"  Depth: {res['depth']} entries")
        click.echo(f"  Total Tree Entries: {res['total_entries']}")
        click.echo(f"  Branch Points: {res['branch_count']}\n")
        for idx, entry in enumerate(res["path"], start=1):
            snippet = entry.get("content", "").replace("\n", " ").strip()
            if len(snippet) > 60:
                snippet = snippet[:57] + "..."
            click.echo(f"  {idx}. [{entry.get('id')}] {entry.get('role')}: {snippet}")
    except Exception as exc:
        raise click.ClickException(str(exc))


@tau_group.command("repair-history")
@click.option(
    "--file",
    "-f",
    "input_file",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="JSON file containing the message array.",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    default=None,
    type=click.Path(dir_okay=False),
    help="Optional path to save repaired messages.",
)
def tau_repair_history(input_file: str, output_file: str | None) -> None:
    """Normalize tool message history to guarantee model provider parity."""
    try:
        raw_text = Path(input_file).read_text(encoding="utf-8")
        messages = json.loads(raw_text)
        if not isinstance(messages, list):
            raise click.BadParameter("Input JSON must contain an array of message objects.")
        res = repair_tool_history_cmd(messages)
        click.echo("Tool History Normalization Complete:")
        click.echo(f"  Modified:           {res['is_modified']}")
        click.echo(f"  Orphans Dropped:    {res['dropped_count']}")
        click.echo(f"  Synthesized Calls:  {res['synthesized_count']}")
        for repair in res["repairs_applied"]:
            click.echo(f"    - {repair}")

        if output_file:
            Path(output_file).write_text(
                json.dumps(res["repaired_messages"], indent=2), encoding="utf-8"
            )
            click.echo(f"\nRepaired messages written to: {output_file}")
    except Exception as exc:
        raise click.ClickException(str(exc))


@tau_group.command("trust-check")
@click.argument("project_path", default=".")
@click.option(
    "--trusted-root",
    "-t",
    "trusted_roots",
    multiple=True,
    help="Explicitly trusted directory root.",
)
def tau_trust_check(project_path: str, trusted_roots: tuple[str, ...]) -> None:
    """Evaluate workspace boundary trust, git root, and sensitive assets."""
    roots = list(trusted_roots) if trusted_roots else None
    res = evaluate_project_trust_cmd(project_path, roots)
    status_sym = "✓ TRUSTED" if res["is_trusted"] else f"✗ {res['permission_level']}"
    click.echo(f"\nWorkspace Trust Audit: {res['project_path']}")
    click.echo("━" * 60)
    click.echo(f"Security Posture: {status_sym}")
    click.echo(f"Git Root:         {res['git_root'] or 'None (Untracked)'}")
    click.echo(f"Permission Tier:  {res['permission_level']}")
    if res["protected_assets"]:
        click.echo(f"Sensitive Assets: {', '.join(res['protected_assets'])}")
    if res["warnings"]:
        click.echo("Warnings:")
        for w in res["warnings"]:
            click.echo(f"  ! {w}")
    click.echo()


@tau_group.command("append-journal")
@click.option(
    "--file",
    "-f",
    "journal_file",
    required=True,
    type=click.Path(dir_okay=False),
    help="Path to the JSONL session journal.",
)
@click.option("--id", "-i", "node_id", required=True, help="Session node ID.")
@click.option(
    "--parent", "-p", "parent_id", default=None, help="Parent session node ID."
)
@click.option(
    "--role",
    "-r",
    default="user",
    type=click.Choice(["user", "assistant", "system", "tool"]),
    help="Message role.",
)
@click.option(
    "--content", "-c", required=True, help="Message text or observation content."
)
def tau_append_journal(
    journal_file: str,
    node_id: str,
    parent_id: str | None,
    role: str,
    content: str,
) -> None:
    """Append a session entry to an advisory locked JSONL journal."""
    try:
        saved = append_journal_entry_cmd(
            journal_path=journal_file,
            node_id=node_id,
            parent_id=parent_id,
            role=role,
            content=content,
        )
        click.echo(f"Appended entry [{saved['id']}] to {journal_file} (role: {saved['role']}).")
    except Exception as exc:
        raise click.ClickException(str(exc))


__all__ = [
    "append_journal_entry_cmd",
    "evaluate_project_trust_cmd",
    "get_tau_service",
    "render_session_tree_cmd",
    "repair_tool_history_cmd",
    "resolve_session_path_cmd",
    "tau_append_journal",
    "tau_group",
    "tau_repair_history",
    "tau_resolve_path",
    "tau_tree",
    "tau_trust_check",
]
