"""Reflection and Knowledge CLI submodule: runner."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import asyncio

import click

from harness.commands._utils import _run_async
from harness.creator.reflection import (
    MemoryPatternPipeline,
    ReflectionReport,
    ReflectionScope,
    resolve_reflector_engine,
)
from harness.services.storage import SQLiteStorageService

from .group import knowledge_group, logger


async def run_reflection_cmd(
    *,
    db_path: str = ":memory:",
    scope: ReflectionScope | None = None,
    since_iso: str | None = None,
    conv_id: str | None = None,
    category: str | None = None,
    test_report_path: Path | str | None = None,
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
                since_dt = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))
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
        engine = resolve_reflector_engine(
            storage=storage,
            temp_dir=temp_dir,
            app_data_dir=app_data_dir,
            pipeline=pipeline,
        )
        report = await engine.reflect(
            scope=scope,
            test_report_path=test_report_path,
            commit_to_vault=commit_to_vault,
            generate_html_brief=generate_html,
            vault_dir=vault_dir,
        )
        return report
    finally:
        storage.close()


@knowledge_group.command("reflect")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option(
    "--since", "since_iso", default=None, help="Filter memory artifacts created on or after this ISO date/timestamp"
)
@click.option("--conv-id", "conv_id", default=None, help="Filter transcript harvesting to a specific conversation ID")
@click.option(
    "--category",
    "category",
    default=None,
    help="Filter distilled heuristics by category (e.g. architecture, performance)",
)
@click.option(
    "--test-report", "test_report", default=None, help="Path to JUnit XML test report or CI artifacts to distill"
)
@click.option(
    "--min-confidence", "min_confidence", default=0.80, type=float, help="Minimum confidence threshold (0.0 - 1.0)"
)
@click.option("--limit", "limit", default=50, type=int, help="Maximum number of reports/transcripts to harvest")
@click.option("--daemon", "daemon", is_flag=True, help="Run continuous background reflection daemon")
@click.option(
    "--interval",
    "interval_seconds",
    default=300.0,
    type=float,
    help="Interval in seconds between daemon distillation cycles",
)
@click.option("--no-html", "no_html", is_flag=True, help="Disable generating interactive HTML visual brief")
@click.option("--no-commit", "no_commit", is_flag=True, help="Do not commit distilled items into the knowledge vault")
def knowledge_reflect(
    vault_dir: str,
    since_iso: str | None,
    conv_id: str | None,
    category: str | None,
    test_report: str | None,
    min_confidence: float,
    limit: int,
    daemon: bool,
    interval_seconds: float,
    no_html: bool,
    no_commit: bool,
) -> None:
    """Reflect on internal history (HTML reports, transcripts, test runs) and distill Knowledge Items."""
    if daemon:
        click.echo(f"Starting continuous reflection daemon (interval: {interval_seconds}s, vault: {vault_dir})...")
        from harness.services.reflection_worker import ReflectionDaemonWorker

        worker = ReflectionDaemonWorker(
            interval_seconds=interval_seconds,
            test_report_path=test_report,
            vault_dir=vault_dir,
            commit_to_vault=not no_commit,
            generate_html=not no_html,
            min_confidence=min_confidence,
        )

        async def _run_daemon() -> None:
            worker.start()
            try:
                while True:
                    await asyncio.sleep(1)
            except (asyncio.CancelledError, KeyboardInterrupt):
                await worker.stop()

        try:
            _run_async(_run_daemon())
        except KeyboardInterrupt:
            click.echo("\nReflection daemon stopped by user.")
        return

    report = _run_async(
        run_reflection_cmd(
            since_iso=since_iso,
            conv_id=conv_id,
            category=category,
            test_report_path=test_report,
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
@click.option(
    "--since", "since_iso", default=None, help="Filter memory artifacts created on or after this ISO date/timestamp"
)
@click.option("--conv-id", "conv_id", default=None, help="Filter transcript harvesting to a specific conversation ID")
@click.option(
    "--category",
    "category",
    default=None,
    help="Filter distilled heuristics by category (e.g. architecture, performance)",
)
@click.option(
    "--test-report", "test_report", default=None, help="Path to JUnit XML test report or CI artifacts to distill"
)
@click.option(
    "--min-confidence", "min_confidence", default=0.80, type=float, help="Minimum confidence threshold (0.0 - 1.0)"
)
@click.option("--limit", "limit", default=50, type=int, help="Maximum number of reports/transcripts to harvest")
@click.option("--daemon", "daemon", is_flag=True, help="Run continuous background reflection daemon")
@click.option(
    "--interval",
    "interval_seconds",
    default=300.0,
    type=float,
    help="Interval in seconds between daemon distillation cycles",
)
@click.option("--no-html", "no_html", is_flag=True, help="Disable generating interactive HTML visual brief")
@click.option("--no-commit", "no_commit", is_flag=True, help="Do not commit distilled items into the knowledge vault")
def reflect_cli(
    vault_dir: str,
    since_iso: str | None,
    conv_id: str | None,
    category: str | None,
    test_report: str | None,
    min_confidence: float,
    limit: int,
    daemon: bool,
    interval_seconds: float,
    no_html: bool,
    no_commit: bool,
) -> None:
    """Run endogenous reflection loop across internal reports and transcripts."""
    knowledge_reflect.callback(
        vault_dir=vault_dir,
        since_iso=since_iso,
        conv_id=conv_id,
        category=category,
        test_report=test_report,
        min_confidence=min_confidence,
        limit=limit,
        daemon=daemon,
        interval_seconds=interval_seconds,
        no_html=no_html,
        no_commit=no_commit,
    )


__all__ = ["run_reflection_cmd", "knowledge_reflect", "reflect_cli"]
