"""Reflection and Knowledge CLI submodule: export_cmds."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import time
import webbrowser

import click

from harness.commands._utils import _run_async
from harness.services.storage import (
    SQLiteStorageService,
    backfill_edges_mechanically,
    export_knowledge_graph,
    resolve_knowledge_graph_service,
    validate_export_path,
)

from .group import knowledge_group


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
        written = export_knowledge_graph(graph, validated_path, format=fmt, dynamic=dynamic_gexf, items=items)
        return graph, written

    graph, written = _run_async(_derive_and_export())
    storage.close()

    s = graph.summary
    non_ki_count = s.total_nodes - s.ki_nodes
    click.echo(f"\n📊 Knowledge Graph Export ({fmt.upper()})")
    click.echo("━" * 70)
    click.echo(f"Target File:           {written}")
    click.echo(f"Total Nodes:           {s.total_nodes} ({s.ki_nodes} KIs, {non_ki_count} external)")
    click.echo(
        f"Total Edges:           {s.total_edges} ({s.asserted_edge_count} asserted, {s.derived_edge_count} derived)"
    )
    for edge_type, count in sorted(s.edges_by_type.items()):
        click.echo(f"  • {edge_type:<20} {count:>4}")
    click.echo(f"Components:            {s.component_count} (Largest: {s.largest_component_size})")
    click.echo(f"Isolated KIs:          {s.isolated_ki_count}")
    click.echo(f"Untagged KIs:          {s.untagged_ki_count}")
    click.echo(f"Uncategorized KIs:     {s.uncategorized_ki_count}")
    if s.excluded_mega_tags:
        click.echo(f"Excluded Mega-Tags:    {', '.join(s.excluded_mega_tags)}")
    click.echo(f"✓ Successfully exported knowledge graph to '{written}'.\n")

    if open_browser:
        webbrowser.open(written.resolve().as_uri())


@knowledge_group.command("backfill")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option("--dry-run", is_flag=True, default=False, help="Display proposed backfill edges without modifying disk")
@click.option(
    "--commit", is_flag=True, default=False, help="Commit backfilled edges non-destructively to metadata.json on disk"
)
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


__all__ = ["knowledge_export", "knowledge_backfill"]
