"""CLI and service commands for endogenous reflection and memory distillation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import structlog

from harness.creator.reflection import (
    HarnessReflectorEngine,
    MemoryPatternPipeline,
    ReflectionReport,
    ReflectionScope,
)
from harness.services.storage import SQLiteStorageService

logger = structlog.get_logger(__name__)


async def run_reflection_cmd(
    *,
    db_path: str = ":memory:",
    scope: ReflectionScope | None = None,
    since_iso: str | None = None,
    conv_id: str | None = None,
    category: str | None = None,
    min_confidence: float = 0.80,
    limit: int = 50,
    commit_to_vault: bool = True,
    generate_html: bool = True,
    vault_dir: Path | str = ".harness/knowledge",
    temp_dir: Path | str | None = None,
    app_data_dir: Path | str | None = None,
    pipeline: MemoryPatternPipeline | None = None,
) -> ReflectionReport:
    """Run an endogenous memory reflection loop and distill knowledge items."""
    # Build or adapt scope
    if scope is None:
        since_dt = None
        if since_iso:
            try:
                since_dt = datetime.fromisoformat(since_iso)
            except Exception as e:
                logger.warning("Invalid since_iso timestamp, ignoring", since=since_iso, error=str(e))

        conv_list = [conv_id] if conv_id else None
        cat_list = [category] if category else None

        scope = ReflectionScope(
            since=since_dt,
            conversation_ids=conv_list,
            categories=cat_list,
            min_confidence=min_confidence,
            limit=limit,
        )

    storage = SQLiteStorageService(db_path=db_path)
    try:
        engine = HarnessReflectorEngine(
            storage=storage,
            temp_dir=temp_dir,
            app_data_dir=app_data_dir,
            pipeline=pipeline,
        )
        report = await engine.reflect(
            scope=scope,
            commit_to_vault=commit_to_vault,
            generate_html_brief=generate_html,
            vault_dir=vault_dir,
        )
        return report
    finally:
        storage.close()


# --- Click CLI adapters ---
import sys
import click
from harness.commands._utils import _run_async


@click.group("knowledge")
def knowledge_group() -> None:
    """Manage and query the distilled Knowledge Vault and Isnad lineage."""
    pass


@knowledge_group.command("sync")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option("--db", "db_path", default=None, help="Path to SQLite storage database (defaults to ~/.harness/storage.db)")
def knowledge_sync(vault_dir: str, db_path: str | None) -> None:
    """Sync all on-disk Knowledge Items from .harness/knowledge/ into the storage database."""
    storage_path = db_path or (Path.home() / ".harness" / "storage.db")
    storage = SQLiteStorageService(storage_path)

    async def _sync():
        count = await storage.sync_knowledge_vault(vault_dir)
        return count

    synced = _run_async(_sync())
    storage.close()
    click.echo(f"✓ Successfully synced {synced} Knowledge Item(s) from '{vault_dir}' into storage.")


@knowledge_group.command("list")
@click.option("--tag", "-t", default=None, help="Filter by tag")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
def knowledge_list(tag: str | None, vault_dir: str) -> None:
    """List all Knowledge Items in storage (hydrates from disk if DB is empty)."""
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


@knowledge_group.command("query")
@click.argument("query_str")
@click.option("--tag", "-t", default=None, help="Filter by tag")
@click.option("--status", "-s", default=None, help="Filter by Isnad status (e.g. VERIFIED)")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
def knowledge_query(query_str: str, tag: str | None, status: str | None, vault_dir: str) -> None:
    """Search Knowledge Items by keyword, tag, or Isnad status."""
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


@knowledge_group.command("verify")
@click.argument("ki_id")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
def knowledge_verify(ki_id: str, vault_dir: str) -> None:
    """Audit Isnad lineage nodes and primary source file existence for a Knowledge Item."""
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


@knowledge_group.command("reflect")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option("--since", "since_iso", default=None, help="Filter memory artifacts created on or after this ISO date/timestamp")
@click.option("--conv-id", "conv_id", default=None, help="Filter transcript harvesting to a specific conversation ID")
@click.option("--category", "category", default=None, help="Filter distilled heuristics by category (e.g. architecture, performance)")
@click.option("--min-confidence", "min_confidence", default=0.80, type=float, help="Minimum confidence threshold (0.0 - 1.0)")
@click.option("--limit", "limit", default=50, type=int, help="Maximum number of reports/transcripts to harvest")
@click.option("--no-html", "no_html", is_flag=True, help="Disable generating interactive HTML visual brief")
@click.option("--no-commit", "no_commit", is_flag=True, help="Do not commit distilled items into the knowledge vault")
def knowledge_reflect(
    vault_dir: str,
    since_iso: str | None,
    conv_id: str | None,
    category: str | None,
    min_confidence: float,
    limit: int,
    no_html: bool,
    no_commit: bool,
) -> None:
    """Reflect on internal history (HTML reports, transcripts) and distill Knowledge Items."""
    report = _run_async(
        run_reflection_cmd(
            since_iso=since_iso,
            conv_id=conv_id,
            category=category,
            min_confidence=min_confidence,
            limit=limit,
            commit_to_vault=not no_commit,
            generate_html=not no_html,
            vault_dir=vault_dir,
        )
    )

    click.echo(f"\n🧠 Endogenous Memory Reflection Report: {report.reflection_id}")
    click.echo("━" * 70)
    click.echo(f"Harvested Reports:     {report.harvested_reports_count}")
    click.echo(f"Harvested Transcripts: {report.harvested_transcripts_count}")
    click.echo(f"Distilled Heuristics:  {len(report.heuristics)}")
    click.echo(f"Committed KIs:         {len(report.knowledge_items)}")

    if report.html_brief_path:
        click.echo(f"\n✓ Generated Visual Reflection Brief: {report.html_brief_path}")

    click.echo("\nDistilled Heuristics Matrix:")
    click.echo("─" * 70)
    for h in report.heuristics:
        click.echo(f"• [{h.category.upper()}] {h.title} (Confidence: {h.confidence * 100:.0f}%)")
        click.echo(f"  Heuristic: {h.heuristic}")
        if h.anti_pattern:
            click.echo(f"  Anti-Pattern: {h.anti_pattern}")
    click.echo()


@click.command("reflect")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option("--since", "since_iso", default=None, help="Filter memory artifacts created on or after this ISO date/timestamp")
@click.option("--conv-id", "conv_id", default=None, help="Filter transcript harvesting to a specific conversation ID")
@click.option("--category", "category", default=None, help="Filter distilled heuristics by category (e.g. architecture, performance)")
@click.option("--min-confidence", "min_confidence", default=0.80, type=float, help="Minimum confidence threshold (0.0 - 1.0)")
@click.option("--limit", "limit", default=50, type=int, help="Maximum number of reports/transcripts to harvest")
@click.option("--no-html", "no_html", is_flag=True, help="Disable generating interactive HTML visual brief")
@click.option("--no-commit", "no_commit", is_flag=True, help="Do not commit distilled items into the knowledge vault")
def reflect_cli(
    vault_dir: str,
    since_iso: str | None,
    conv_id: str | None,
    category: str | None,
    min_confidence: float,
    limit: int,
    no_html: bool,
    no_commit: bool,
) -> None:
    """Run endogenous reflection loop across internal reports and transcripts."""
    knowledge_reflect.callback(
        vault_dir=vault_dir,
        since_iso=since_iso,
        conv_id=conv_id,
        category=category,
        min_confidence=min_confidence,
        limit=limit,
        no_html=no_html,
        no_commit=no_commit,
    )


__all__ = [
    "knowledge_group",
    "knowledge_list",
    "knowledge_query",
    "knowledge_reflect",
    "knowledge_sync",
    "knowledge_verify",
    "reflect_cli",
    "run_reflection_cmd",
]
