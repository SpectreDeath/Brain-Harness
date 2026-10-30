"""CLI and service commands for endogenous reflection and memory distillation."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime
import json
from pathlib import Path
import tempfile
import time
import webbrowser

import structlog

from harness.creator.reflection import (
    HarnessReflectorEngine,
    MemoryPatternPipeline,
    ReflectionReport,
    ReflectionScope,
    resolve_reflector_engine,
)
from harness.services.storage import (
    SQLiteStorageService,
    audit_vault_hygiene,
    backfill_edges_mechanically,
    export_knowledge_graph,
    resolve_knowledge_graph_service,
    suggest_category_for_item,
    suggest_tags_for_item,
    validate_export_path,
)

logger = structlog.get_logger(__name__)


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
@click.option("--test-report", "test_report", default=None, help="Path to JUnit XML test report or CI artifacts to distill")
@click.option("--min-confidence", "min_confidence", default=0.80, type=float, help="Minimum confidence threshold (0.0 - 1.0)")
@click.option("--limit", "limit", default=50, type=int, help="Maximum number of reports/transcripts to harvest")
@click.option("--daemon", "daemon", is_flag=True, help="Run continuous background reflection daemon")
@click.option("--interval", "interval_seconds", default=300.0, type=float, help="Interval in seconds between daemon distillation cycles")
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


@knowledge_group.command("contradictions")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
def knowledge_contradictions(vault_dir: str) -> None:
    """Audit Knowledge Vault for contradictory claims, polarity antinomies, and supersessions."""
    storage = SQLiteStorageService(":memory:")

    async def _audit():
        await storage.sync_knowledge_vault(vault_dir)
        return await storage.audit_contradictions()

    review_items = _run_async(_audit())
    storage.close()

    if not review_items:
        click.echo("\n✓ No contradictory claims or antinomies detected across the Knowledge Vault.")
        return

    click.echo(f"\nKnowledge Vault Contradiction Review Queue ({len(review_items)} flagged pairs):\n" + "━" * 70)
    for idx, item in enumerate(review_items, 1):
        click.echo(f"[{idx}] {item.conflict_type.upper()} (Confidence: {item.confidence:.0%})")
        click.echo(f"    KI A: {item.ki_a} ('{item.title_a[:50]}')")
        click.echo(f"          Claim: \"{item.assertion_a[:80]}\"")
        click.echo(f"    KI B: {item.ki_b} ('{item.title_b[:50]}')")
        click.echo(f"          Claim: \"{item.assertion_b[:80]}\"")
        click.echo(f"    Reason: {item.reason}")
        click.echo(f"    Suggested Edge: {item.suggested_edge}\n")


@knowledge_group.command("lineage")
@click.argument("skill_name")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
def knowledge_lineage(skill_name: str, vault_dir: str) -> None:
    """Trace all Knowledge Items that contributed to or were distilled into a skill."""
    from harness.services.storage.vault_graph import KnowledgeGraphQueryService
    storage = SQLiteStorageService(":memory:")

    async def _lineage():
        await storage.sync_knowledge_vault(vault_dir)
        items = await storage.list_knowledge_items()
        graph = KnowledgeGraphQueryService()
        return graph.get_skill_lineage(skill_name, items), items

    ki_ids, all_items = _run_async(_lineage())
    storage.close()

    click.echo(f"\nLineage for Skill '{skill_name}' ({len(ki_ids)} source KIs):\n" + "━" * 70)
    if not ki_ids:
        click.echo("  (No direct lineage edges recorded)")
    else:
        id_map = {item.id: item for item in all_items}
        for ki_id in ki_ids:
            item = id_map.get(ki_id)
            title = item.title if item else "Unknown"
            click.echo(f"  • {ki_id:<25} {title}")
    click.echo()


@knowledge_group.command("export")
@click.option(
    "--format",
    "-f",
    "export_format",
    type=click.Choice(["json", "gexf", "graphml", "html", "cypher"], case_sensitive=False),
    default="json",
    help="Export serialization format (default: json)",
)
@click.option(
    "--out",
    "-o",
    "out_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Target file path (defaults to outputs/knowledge_graph.<format> or %TEMP% for --open)",
)
@click.option(
    "--nodes",
    "nodes_filter",
    type=click.Choice(["all", "ki-only"], case_sensitive=False),
    default="all",
    help="Materialize all entities or filter strictly to Knowledge Items",
)
@click.option(
    "--include-single-tag-edges",
    is_flag=True,
    default=False,
    help="Derive edges between items sharing a single non-mega tag",
)
@click.option(
    "--include-shared-source",
    is_flag=True,
    default=False,
    help="Derive edges between items citing the same code or repository source",
)
@click.option(
    "--max-tag-freq",
    type=float,
    default=0.15,
    help="Tag frequency ratio (0.0 - 1.0) above which tags are excluded as mega-tags",
)
@click.option(
    "--min-confidence",
    type=float,
    default=0.0,
    help="Minimum edge confidence threshold",
)
@click.option(
    "--vault",
    "-v",
    "vault_dir",
    default=".harness/knowledge",
    help="Path to knowledge vault root directory",
)
@click.option(
    "--dynamic",
    "dynamic_gexf",
    is_flag=True,
    default=False,
    help="Enable dynamic temporal attributes (start/end dates) for GEXF export",
)
@click.option(
    "--open",
    "open_browser",
    is_flag=True,
    default=False,
    help="Automatically open generated HTML brief or export in browser/viewer",
)
def knowledge_export(
    export_format: str,
    out_path: Path | None,
    nodes_filter: str,
    include_single_tag_edges: bool,
    include_shared_source: bool,
    max_tag_freq: float,
    min_confidence: float,
    vault_dir: str,
    dynamic_gexf: bool,
    open_browser: bool,
) -> None:
    """Export derived knowledge graph to JSON, GEXF, GraphML, or standalone interactive HTML."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    fmt = export_format.lower()
    if out_path is None:
        if open_browser:
            out_path = Path(tempfile.gettempdir()) / f"knowledge-graph-{int(time.time())}.{fmt}"
        else:
            out_path = Path("outputs") / f"knowledge_graph.{fmt}"

    try:
        validated_path = validate_export_path(out_path, vault_dir=vault_dir)
    except ValueError as e:
        click.echo(f"✗ Export path error: {e}", err=True)
        sys.exit(1)

    storage = SQLiteStorageService(":memory:")

    async def _derive_and_export():
        await storage.sync_knowledge_vault(vault_dir)
        items = await storage.list_knowledge_items()
        graph_svc = resolve_knowledge_graph_service()
        graph = graph_svc.derive_graph(
            items,
            nodes_filter=nodes_filter,
            include_single_tag_edges=include_single_tag_edges,
            include_shared_source=include_shared_source,
            max_tag_freq=max_tag_freq,
            min_confidence=min_confidence,
        )
        written = export_knowledge_graph(graph, validated_path, format=fmt, dynamic=dynamic_gexf)
        return graph, written

    graph, written = _run_async(_derive_and_export())
    storage.close()

    s = graph.summary
    non_ki_count = s.total_nodes - s.ki_nodes
    click.echo(f"\n📊 Knowledge Graph Export ({fmt.upper()})")
    click.echo("━" * 70)
    click.echo(f"Target File:           {written}")
    click.echo(f"Total Nodes:           {s.total_nodes} ({s.ki_nodes} KIs, {non_ki_count} external)")
    click.echo(f"Total Edges:           {s.total_edges} ({s.asserted_edge_count} asserted, {s.derived_edge_count} derived)")
    click.echo(f"Components:            {s.component_count} (Largest: {s.largest_component_size})")
    click.echo(f"Isolated KIs:          {s.isolated_ki_count}")
    if s.excluded_mega_tags:
        click.echo(f"Excluded Mega-Tags:    {', '.join(s.excluded_mega_tags)}")
    click.echo(f"✓ Successfully exported knowledge graph to '{written}'.\n")

    if open_browser:
        webbrowser.open(written.resolve().as_uri())


@knowledge_group.command("backfill")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option("--dry-run", is_flag=True, default=False, help="Display proposed backfill edges without modifying disk")
@click.option("--commit", is_flag=True, default=False, help="Commit backfilled edges non-destructively to metadata.json on disk")
@click.option("--max-tag-freq", default=0.15, type=float, help="Tag frequency threshold for mega-tag exclusion")
def knowledge_backfill(vault_dir: str, dry_run: bool, commit: bool, max_tag_freq: float) -> None:
    """Mechanically backfill references_code, became_skill, became_plugin, supersedes, and same_domain edges."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    is_dry_run = dry_run or not commit
    storage = SQLiteStorageService(":memory:")

    async def _backfill():
        await storage.sync_knowledge_vault(vault_dir)
        items = await storage.list_knowledge_items()
        before_count = sum(len(ki.edges) for ki in items)

        res = backfill_edges_mechanically(
            items,
            vault_dir=vault_dir,
            max_tag_freq=max_tag_freq,
            dry_run=is_dry_run,
        )

        after_count = sum(len(ki.edges) for ki in items)

        if commit and not dry_run:
            for ki in items:
                await storage.export_single_item(ki, vault_dir=vault_dir)

        return items, before_count, after_count, res

    items, before_count, after_count, res = _run_async(_backfill())
    storage.close()

    status_str = "DRY RUN (no files modified)" if is_dry_run else f"COMMITTED to '{vault_dir}'"
    click.echo(f"\n🔄 Knowledge Vault Edge Backfill [{status_str}]")
    click.echo("━" * 70)
    click.echo(f"Total Items Audited:   {len(items)}")
    click.echo(f"Items Updated:         {res['items_updated_count']}")
    click.echo(f"Edges Before:          {before_count}")
    click.echo(f"Edges Added / Proposed:{res['total_added']}")
    click.echo(f"Edges Total:           {before_count + res['total_added']}")
    click.echo("\nBreakdown of Added / Proposed Edges:")
    for edge_type, count in sorted(res["added_by_type"].items()):
        click.echo(f"  • {edge_type:<20} {count:>4}")

    if is_dry_run:
        click.echo("\nRun with '--commit' to persist these edges to metadata.json on disk.\n")
    else:
        click.echo(f"\n✓ Successfully persisted {res['total_added']} edges to on-disk vault.\n")


@knowledge_group.command("lifecycle")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option("--min-retrievals", default=5, type=int, help="Minimum retrievals before evaluating promote/demote")
@click.option("--promote-ratio", default=0.75, type=float, help="Success ratio threshold for promotion")
@click.option("--demote-ratio", default=0.25, type=float, help="Success ratio threshold for demotion")
@click.option("--apply-contradictions", is_flag=True, default=False, help="Display contradiction queue alongside lifecycle audit")
def knowledge_lifecycle(
    vault_dir: str,
    min_retrievals: int,
    promote_ratio: float,
    demote_ratio: float,
    apply_contradictions: bool,
) -> None:
    """Evaluate retrieval success rates and update item lifecycle status (PROMOTED / DEMOTED)."""
    storage = SQLiteStorageService(":memory:")

    async def _lifecycle():
        await storage.sync_knowledge_vault(vault_dir)
        lifecycle_res = await storage.evaluate_vault_lifecycle(
            min_retrievals=min_retrievals,
            promote_ratio=promote_ratio,
            demote_ratio=demote_ratio,
            vault_dir=vault_dir,
        )
        conflicts = await storage.audit_contradictions()
        return lifecycle_res, conflicts

    res, conflicts = _run_async(_lifecycle())
    storage.close()

    click.echo("\n📈 Knowledge Vault Lifecycle Evaluation")
    click.echo("━" * 70)
    promoted = res.get("promoted", [])
    demoted = res.get("demoted", [])
    click.echo(f"Promoted to PROMOTED:  {len(promoted)} item(s)")
    for p in promoted:
        click.echo(f"  ✓ {p}")
    click.echo(f"Demoted to DEMOTED:    {len(demoted)} item(s)")
    for d in demoted:
        click.echo(f"  ✗ {d}")

    if not promoted and not demoted:
        click.echo("  (No items crossed the retrieval/utility threshold)")

    if apply_contradictions or conflicts:
        click.echo(f"\nContradiction Review Queue ({len(conflicts)} flagged pair(s)):")
        click.echo("─" * 70)
        for idx, item in enumerate(conflicts, 1):
            click.echo(f"[{idx}] {item.conflict_type.upper()} (Confidence: {item.confidence:.0%})")
            click.echo(f"    KI A: {item.ki_a} | KI B: {item.ki_b}")
            click.echo(f"    Reason: {item.reason}")
            click.echo(f"    Suggested Resolution: harness knowledge resolve {item.ki_a} {item.ki_b} --action {item.suggested_edge}\n")


@knowledge_group.command("resolve")
@click.argument("ki_a")
@click.argument("ki_b")
@click.option(
    "--action",
    type=click.Choice(["supersede", "contradict", "dismiss"], case_sensitive=False),
    required=True,
    help="Resolution action: supersede (ki_a supersedes ki_b), contradict (mutual conflict), dismiss (ignore)",
)
@click.option("--reason", default="", help="Optional notes or justification for resolution")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
def knowledge_resolve(ki_a: str, ki_b: str, action: str, reason: str, vault_dir: str) -> None:
    """Resolve a contradiction or antinomy between two Knowledge Items on disk."""
    storage = SQLiteStorageService(":memory:")

    async def _resolve():
        await storage.sync_knowledge_vault(vault_dir)
        item_a = await storage.get_knowledge_item(ki_a)
        item_b = await storage.get_knowledge_item(ki_b)
        if not item_a:
            raise click.ClickException(f"Knowledge Item '{ki_a}' not found in vault '{vault_dir}'")
        if not item_b:
            raise click.ClickException(f"Knowledge Item '{ki_b}' not found in vault '{vault_dir}'")

        act = action.lower()
        if act == "supersede":
            item_a.add_edge("supersedes", item_b.id, target_kind="ki", derived=False, confidence=1.0, description=reason or "Manual resolution")
            item_b.status = "SUPERSEDED"
            item_b.superseded_by = item_a.id
            await storage.save_knowledge_item(item_a, vault_dir=vault_dir)
            await storage.save_knowledge_item(item_b, vault_dir=vault_dir)
            await storage.export_single_item(item_a, vault_dir=vault_dir)
            await storage.export_single_item(item_b, vault_dir=vault_dir)
            return f"✓ Marked '{item_b.id}' SUPERSEDED by '{item_a.id}' with directed 'supersedes' edge."
        elif act == "contradict":
            item_a.add_edge("contradicts", item_b.id, target_kind="ki", derived=False, confidence=1.0, description=reason or "Manual resolution")
            item_b.add_edge("contradicts", item_a.id, target_kind="ki", derived=False, confidence=1.0, description=reason or "Manual resolution")
            item_a.status = "CHALLENGED"
            item_b.status = "CHALLENGED"
            await storage.save_knowledge_item(item_a, vault_dir=vault_dir)
            await storage.save_knowledge_item(item_b, vault_dir=vault_dir)
            await storage.export_single_item(item_a, vault_dir=vault_dir)
            await storage.export_single_item(item_b, vault_dir=vault_dir)
            return f"✓ Recorded mutual 'contradicts' edges between '{item_a.id}' and '{item_b.id}'; status updated to CHALLENGED."
        else:
            return f"✓ Dismissed contradiction between '{item_a.id}' and '{item_b.id}' (no changes written)."

    msg = _run_async(_resolve())
    storage.close()
    click.echo(f"\n{msg}\n")


@knowledge_group.command("stats")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output raw census metrics in JSON format")
@click.option("--max-tag-freq", default=0.15, type=float, help="Tag frequency threshold for mega-tag exclusion")
def knowledge_stats(vault_dir: str, as_json: bool, max_tag_freq: float) -> None:
    """Print comprehensive knowledge graph census metrics, node kinds, edge types, and components."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    storage = SQLiteStorageService(":memory:")

    async def _stats():
        await storage.sync_knowledge_vault(vault_dir)
        items = await storage.list_knowledge_items()
        graph_svc = resolve_knowledge_graph_service()
        graph = graph_svc.derive_graph(items, max_tag_freq=max_tag_freq)
        return graph.summary

    summary = _run_async(_stats())
    storage.close()

    if as_json:
        click.echo(json.dumps(summary.to_dict(), indent=2))
        return

    s = summary
    non_ki_count = s.total_nodes - s.ki_nodes
    click.echo("\n📊 Knowledge Graph Census Statistics")
    click.echo("━" * 70)
    click.echo(f"Total Entities:        {s.total_nodes} ({s.ki_nodes} KIs, {non_ki_count} external)")
    for kind, count in sorted(s.non_ki_nodes_by_kind.items()):
        click.echo(f"  • {kind:<20} {count:>4}")
    click.echo(f"Total Edges:           {s.total_edges} ({s.asserted_edge_count} asserted, {s.derived_edge_count} derived)")
    for edge_type, count in sorted(s.edges_by_type.items()):
        click.echo(f"  • {edge_type:<20} {count:>4}")
    click.echo(f"Connected Components:  {s.component_count} (Largest: {s.largest_component_size} nodes)")
    click.echo(f"Isolated KIs:          {s.isolated_ki_count}")
    click.echo(f"Untagged KIs:          {s.untagged_ki_count}")
    click.echo(f"Uncategorized KIs:     {s.uncategorized_ki_count}")
    click.echo(f"Date Coverage:         {s.date_coverage_count} / {s.ki_nodes} ({s.date_coverage_count / max(1, s.ki_nodes):.1%})")
    if s.excluded_mega_tags:
        click.echo(f"Excluded Mega-Tags:    {', '.join(s.excluded_mega_tags)}")
    click.echo()


@knowledge_group.command("neighbors")
@click.argument("node_id")
@click.option("--depth", "-d", default=1, type=int, help="Neighborhood traversal depth (1..4)")
@click.option("--edge-type", "-t", default=None, help="Filter by specific edge relationship type")
@click.option("--exclude-derived", is_flag=True, default=False, help="Exclude automatically derived edges")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
def knowledge_neighbors(node_id: str, depth: int, edge_type: str | None, exclude_derived: bool, vault_dir: str) -> None:
    """List adjacent Knowledge Items, skills, plugins, and code paths connected to a node."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    storage = SQLiteStorageService(":memory:")

    async def _neighbors():
        await storage.sync_knowledge_vault(vault_dir)
        items = await storage.list_knowledge_items()
        graph_svc = resolve_knowledge_graph_service()
        graph = graph_svc.derive_graph(items)
        neighbors = graph_svc.get_neighbors(
            node_id,
            graph,
            depth=depth,
            edge_type=edge_type,
            exclude_derived=exclude_derived,
        )
        return neighbors

    neighbors = _run_async(_neighbors())
    storage.close()

    click.echo(f"\nNeighborhood for '{node_id}' (Depth: {depth}, {len(neighbors)} adjacent entities):\n" + "━" * 70)
    if not neighbors:
        click.echo("  (No connected neighbors found within specified constraints)")
    else:
        for n in neighbors:
            arr = "→" if n["direction"] == "outbound" else "←"
            der = "[derived]" if n["derived"] else "[asserted]"
            click.echo(f"  {arr} {n['edge_type']:<16} {n['id']:<32} ({n['node_kind']}) {der} {n['confidence']:.0%}")
    click.echo()


@knowledge_group.command("path")
@click.argument("from_id")
@click.argument("to_id")
@click.option("--max-depth", default=6, type=int, help="Maximum search hops (default: 6)")
@click.option("--exclude-derived", is_flag=True, default=False, help="Exclude automatically derived edges")
@click.option("--directed", is_flag=True, default=False, help="Enforce strict directional edge traversal")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
def knowledge_path(from_id: str, to_id: str, max_depth: int, exclude_derived: bool, directed: bool, vault_dir: str) -> None:
    """Find the BFS shortest path between two graph entities (Rule 55: zero synthetic edges)."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    storage = SQLiteStorageService(":memory:")

    async def _path():
        await storage.sync_knowledge_vault(vault_dir)
        items = await storage.list_knowledge_items()
        graph_svc = resolve_knowledge_graph_service()
        graph = graph_svc.derive_graph(items)
        res = graph_svc.find_path(
            from_id,
            to_id,
            graph,
            max_depth=max_depth,
            exclude_derived=exclude_derived,
            directed=directed,
        )
        return res

    res = _run_async(_path())
    storage.close()

    click.echo(f"\nPath Search: '{from_id}' → '{to_id}'\n" + "━" * 70)
    if res["status"] == "no_path":
        click.echo(f"✗ No path found within {max_depth} hops (Rule 55: reachability is strict; no synthetic edges).")
    elif res["status"] == "same_node":
        click.echo("✓ Source and target refer to the same node (0 hops).")
    else:
        click.echo(f"✓ Shortest path found ({res['length']} hops): {' → '.join(res['chain'])}\n")
        for idx, h in enumerate(res["hops"], 1):
            der = "[derived]" if h["derived"] else "[asserted]"
            dir_arrow = "→" if h["direction"] == "forward" else "←"
            click.echo(f"  [{idx}] {h['from']} {dir_arrow} [{h['edge_type']}] {dir_arrow} {h['to']} {der} ({h['confidence']:.0%})")
    click.echo()


@knowledge_group.command("topic")
@click.argument("topic_str")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
def knowledge_topic(topic_str: str, vault_dir: str) -> None:
    """Explore the topic neighborhood: matching KIs, linked skills, and referenced code paths."""
    storage = SQLiteStorageService(":memory:")

    async def _topic():
        await storage.sync_knowledge_vault(vault_dir)
        items = await storage.list_knowledge_items()
        graph_svc = resolve_knowledge_graph_service()
        return graph_svc.get_topic_neighborhood(topic_str, items)

    res = _run_async(_topic())
    storage.close()

    click.echo(f"\nTopic Neighborhood: '{topic_str}' ({len(res['matched_kis'])} matching KIs)\n" + "━" * 70)
    if not res["matched_kis"]:
        click.echo("  (No Knowledge Items match this topic query)")
    else:
        click.echo("Matched Knowledge Items:")
        for ki in res["matched_kis"]:
            click.echo(f"  • {ki}")
        if res["skills"]:
            click.echo("\nLinked Agent Skills:")
            for s in res["skills"]:
                click.echo(f"  ★ {s}")
        if res["paths"]:
            click.echo("\nReferenced Code Paths:")
            for p in res["paths"]:
                click.echo(f"  ⚡ {p}")
    click.echo()


@knowledge_group.command("dependents")
@click.argument("node_id")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
def knowledge_dependents(node_id: str, vault_dir: str) -> None:
    """List inbound dependents pointing to a specific Knowledge Item, skill, or code path."""
    storage = SQLiteStorageService(":memory:")

    async def _dependents():
        await storage.sync_knowledge_vault(vault_dir)
        items = await storage.list_knowledge_items()
        graph_svc = resolve_knowledge_graph_service()
        return graph_svc.get_dependents(node_id, items)

    deps = _run_async(_dependents())
    storage.close()

    click.echo(f"\nInbound Dependents for '{node_id}' ({len(deps)} source items):\n" + "━" * 70)
    if not deps:
        click.echo("  (No items declare inbound edges to this node)")
    else:
        for d in deps:
            click.echo(f"  • {d['source_ki']:<25} ──[{d['edge_type']}]──> ({d['confidence']:.0%})")
    click.echo()


@knowledge_group.command("orphans")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output orphan diagnostics in JSON format")
def knowledge_orphans(vault_dir: str, as_json: bool) -> None:
    """Identify isolated Knowledge Items and report missing-field triage profiles."""
    storage = SQLiteStorageService(":memory:")

    async def _orphans():
        await storage.sync_knowledge_vault(vault_dir)
        items = await storage.list_knowledge_items()
        graph_svc = resolve_knowledge_graph_service()
        graph = graph_svc.derive_graph(items)
        return graph_svc.get_orphans(graph, items)

    orphans = _run_async(_orphans())
    storage.close()

    if as_json:
        click.echo(json.dumps(orphans, indent=2))
        return

    click.echo(f"\n🔍 Knowledge Vault Isolated Entity Triage ({orphans['isolated_count']} items)\n" + "━" * 70)
    prof = orphans["profiles"]
    click.echo(f"Missing-Field Profile: {prof['untagged']} untagged, {prof['uncategorized']} uncategorized, {prof['missing_source']} missing source\n")
    for item in orphans["isolated_items"][:25]:
        cat = item["category"] or "uncategorized"
        src = "src✓" if item["has_source"] else "no-src"
        click.echo(f"  • {item['id']:<26} [{cat:<24}] ({item['tags_count']} tags, {src}) {item['title'][:40]}")
    if orphans["isolated_count"] > 25:
        click.echo(f"\n  ... and {orphans['isolated_count'] - 25} more (use --json for full list)")
    click.echo()


@knowledge_group.command("hygiene")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option("--suggest-categories/--no-suggest-categories", default=True, help="Propose canonical TaxonomyDomain for uncategorized items")
@click.option("--suggest-tags/--no-suggest-tags", default=True, help="Propose 2-5 high-signal domain tags for untagged items")
@click.option("--apply", "apply_changes", is_flag=True, default=False, help="Persist proposed category and tag updates to metadata.json on disk")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output hygiene proposals in JSON format")
def knowledge_hygiene(
    vault_dir: str,
    suggest_categories: bool,
    suggest_tags: bool,
    apply_changes: bool,
    as_json: bool,
) -> None:
    """Audit and mechanically triage uncategorized items and untagged items."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    storage = SQLiteStorageService(":memory:")

    async def _hygiene():
        await storage.sync_knowledge_vault(vault_dir)
        items = await storage.list_knowledge_items()
        audit_res = audit_vault_hygiene(items)

        updated_categories = 0
        updated_tags = 0

        if apply_changes:
            for ki in items:
                modified = False
                if suggest_categories and (not ki.category or ki.category == "general"):
                    new_cat = suggest_category_for_item(ki)
                    if new_cat and new_cat != ki.category:
                        ki.category = new_cat
                        modified = True
                        updated_categories += 1

                if suggest_tags and not ki.tags:
                    new_tags = suggest_tags_for_item(ki)
                    if new_tags:
                        ki.tags = new_tags
                        modified = True
                        updated_tags += 1

                if modified:
                    await storage.save_knowledge_item(ki, vault_dir=vault_dir)
                    await storage.export_single_item(ki, vault_dir=vault_dir)

        return items, audit_res, updated_categories, updated_tags

    items, audit_res, cat_updates, tag_updates = _run_async(_hygiene())
    storage.close()

    if as_json:
        payload = {
            "audit": audit_res,
            "applied": apply_changes,
            "updated_categories": cat_updates,
            "updated_tags": tag_updates,
        }
        click.echo(json.dumps(payload, indent=2))
        return

    click.echo(f"\n🧹 Knowledge Vault Hygiene & Triaging")
    click.echo("━" * 70)
    click.echo(f"Total Items Audited:     {len(items)}")
    click.echo(f"Uncategorized Items:     {audit_res['uncategorized_count']}")
    click.echo(f"Untagged Items:          {audit_res['untagged_count']}")

    if suggest_categories and audit_res["uncategorized"]:
        click.echo(f"\nProposed Category Assignments (showing up to 20):")
        for u in audit_res["uncategorized"][:20]:
            click.echo(f"  • {u['id']:<32} {u['current_category']} ──> {u['proposed_category']}")
        if len(audit_res["uncategorized"]) > 20:
            click.echo(f"    ... and {len(audit_res['uncategorized']) - 20} more (use --json)")

    if suggest_tags and audit_res["untagged"]:
        click.echo(f"\nProposed Tag Assignments (showing up to 15):")
        for u in audit_res["untagged"][:15]:
            tags_str = ", ".join(u["proposed_tags"])
            click.echo(f"  • {u['id']:<32} [{tags_str}]")
        if len(audit_res["untagged"]) > 15:
            click.echo(f"    ... and {len(audit_res['untagged']) - 15} more (use --json)")

    if apply_changes:
        click.echo(f"\n✓ Successfully applied hygiene updates: {cat_updates} categories updated, {tag_updates} tag sets assigned.\n")
    else:
        click.echo("\nRun with '--apply' to persist these updates non-destructively to metadata.json on disk.\n")


@knowledge_group.command("timeline")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output timeline metrics in JSON format")
def knowledge_timeline(vault_dir: str, as_json: bool) -> None:
    """Report data-driven temporal growth metrics, weekly velocity, and domain emergence order."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    storage = SQLiteStorageService(":memory:")

    async def _timeline():
        await storage.sync_knowledge_vault(vault_dir)
        items = await storage.list_knowledge_items()

        weekly_counts = defaultdict(int)
        domain_first_seen = {}
        dated_items = 0

        sorted_items = sorted(
            [ki for ki in items if ki.created_at],
            key=lambda x: x.created_at,
        )

        for ki in sorted_items:
            dated_items += 1
            dt_str = ki.created_at[:10]
            try:
                dt = datetime.fromisoformat(ki.created_at.replace("Z", "+00:00"))
                yw = f"{dt.year}-W{dt.isocalendar().week:02d}"
            except Exception:
                yw = dt_str[:7]
            weekly_counts[yw] += 1
            dom = ki.category or "general"
            if dom not in domain_first_seen:
                domain_first_seen[dom] = {"first_ki": ki.id, "date": dt_str}

        return {
            "total_items": len(items),
            "dated_items": dated_items,
            "weekly_growth": dict(sorted(weekly_counts.items())),
            "domain_emergence": domain_first_seen,
        }

    data = _run_async(_timeline())
    storage.close()

    if as_json:
        click.echo(json.dumps(data, indent=2))
        return

    click.echo(f"\n📅 Knowledge Vault Temporal Growth Report")
    click.echo("━" * 70)
    click.echo(f"Total Vault Items:       {data['total_items']}")
    click.echo(f"Dated Items:             {data['dated_items']} / {data['total_items']} ({data['dated_items'] / max(1, data['total_items']):.1%})")

    click.echo("\nDomain Emergence Order:")
    for dom, info in sorted(data["domain_emergence"].items(), key=lambda x: x[1]["date"]):
        click.echo(f"  • {info['date']}  {dom:<30} (First: {info['first_ki']})")

    click.echo("\nWeekly Creation Velocity:")
    cum = 0
    for yw, cnt in data["weekly_growth"].items():
        cum += cnt
        bar = "█" * min(30, cnt)
        click.echo(f"  • {yw}: {cnt:>3} items {bar:<30} (Cumulative: {cum})")
    click.echo()


@click.command("reflect")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option("--since", "since_iso", default=None, help="Filter memory artifacts created on or after this ISO date/timestamp")
@click.option("--conv-id", "conv_id", default=None, help="Filter transcript harvesting to a specific conversation ID")
@click.option("--category", "category", default=None, help="Filter distilled heuristics by category (e.g. architecture, performance)")
@click.option("--test-report", "test_report", default=None, help="Path to JUnit XML test report or CI artifacts to distill")
@click.option("--min-confidence", "min_confidence", default=0.80, type=float, help="Minimum confidence threshold (0.0 - 1.0)")
@click.option("--limit", "limit", default=50, type=int, help="Maximum number of reports/transcripts to harvest")
@click.option("--daemon", "daemon", is_flag=True, help="Run continuous background reflection daemon")
@click.option("--interval", "interval_seconds", default=300.0, type=float, help="Interval in seconds between daemon distillation cycles")
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


__all__ = [
    "knowledge_backfill",
    "knowledge_contradictions",
    "knowledge_dependents",
    "knowledge_export",
    "knowledge_group",
    "knowledge_hygiene",
    "knowledge_lifecycle",
    "knowledge_lineage",
    "knowledge_list",
    "knowledge_neighbors",
    "knowledge_orphans",
    "knowledge_path",
    "knowledge_query",
    "knowledge_reflect",
    "knowledge_resolve",
    "knowledge_stats",
    "knowledge_sync",
    "knowledge_timeline",
    "knowledge_topic",
    "knowledge_verify",
    "reflect_cli",
    "run_reflection_cmd",
]
