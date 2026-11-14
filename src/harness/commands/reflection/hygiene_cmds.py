"""Reflection and Knowledge CLI submodule: hygiene_cmds."""

from __future__ import annotations

import json
import sys

import click

from harness.commands._utils import _run_async
from harness.services.storage import (
    SQLiteStorageService,
    audit_vault_hygiene,
    resolve_knowledge_graph_service,
    suggest_category_for_item,
    suggest_tags_for_item,
)

from .group import knowledge_group


@knowledge_group.command("stats")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output raw census metrics in JSON format")
@click.option(
    "--include-single-tag-edges", is_flag=True, default=False, help="Include 1-shared-tag derived same_domain edges"
)
@click.option("--include-shared-source", is_flag=True, default=False, help="Include shared_source derived edges")
@click.option("--max-tag-freq", default=0.15, type=float, help="Tag frequency threshold for mega-tag exclusion")
def knowledge_stats(
    vault_dir: str,
    as_json: bool,
    include_single_tag_edges: bool,
    include_shared_source: bool,
    max_tag_freq: float,
) -> None:
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
        graph = graph_svc.derive_graph(
            items,
            include_single_tag_edges=include_single_tag_edges,
            include_shared_source=include_shared_source,
            max_tag_freq=max_tag_freq,
        )
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
    click.echo(
        f"Total Edges:           {s.total_edges} ({s.asserted_edge_count} asserted, {s.derived_edge_count} derived)"
    )
    for edge_type, count in sorted(s.edges_by_type.items()):
        click.echo(f"  • {edge_type:<20} {count:>4}")
    click.echo(f"Connected Components:  {s.component_count} (Largest: {s.largest_component_size} nodes)")
    click.echo(
        f"  • KI-only Components:{s.ki_only_component_count:>4} (Largest: {s.ki_only_largest_component_size} KIs)"
    )
    click.echo(f"Isolated KIs:          {s.isolated_ki_count} (KI-only isolated: {s.ki_only_isolated_count})")
    click.echo(f"Untagged KIs:          {s.untagged_ki_count}")
    click.echo(f"Uncategorized KIs:     {s.uncategorized_ki_count}")
    click.echo(
        f"Date Coverage:         {s.date_coverage_count} / {s.ki_nodes} ({s.date_coverage_count / max(1, s.ki_nodes):.1%})"
    )
    if s.date_sources:
        src_parts = [f"{count} from {src}" for src, count in sorted(s.date_sources.items())]
        click.echo(f"  • Date Sources:      {', '.join(src_parts)}")
    if s.excluded_mega_tags:
        click.echo(f"Excluded Mega-Tags:    {', '.join(s.excluded_mega_tags)}")
    click.echo()


@knowledge_group.command("hygiene")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option(
    "--suggest-categories/--no-suggest-categories",
    default=True,
    help="Propose canonical TaxonomyDomain for uncategorized items",
)
@click.option(
    "--suggest-tags/--no-suggest-tags", default=True, help="Propose 2-5 high-signal domain tags for untagged items"
)
@click.option(
    "--apply",
    "apply_changes",
    is_flag=True,
    default=False,
    help="Persist proposed category and tag updates to metadata.json on disk",
)
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

    click.echo("\n🧹 Knowledge Vault Hygiene & Triaging")
    click.echo("━" * 70)
    click.echo(f"Total Items Audited:     {len(items)}")
    click.echo(f"Uncategorized Items:     {audit_res['uncategorized_count']}")
    click.echo(f"Untagged Items:          {audit_res['untagged_count']}")

    if suggest_categories and audit_res["uncategorized"]:
        click.echo("\nProposed Category Assignments (showing up to 20):")
        for u in audit_res["uncategorized"][:20]:
            click.echo(f"  • {u['id']:<32} {u['current_category']} ──> {u['proposed_category']}")
        if len(audit_res["uncategorized"]) > 20:
            click.echo(f"    ... and {len(audit_res['uncategorized']) - 20} more (use --json)")

    if suggest_tags and audit_res["untagged"]:
        click.echo("\nProposed Tag Assignments (showing up to 15):")
        for u in audit_res["untagged"][:15]:
            tags_str = ", ".join(u["proposed_tags"])
            click.echo(f"  • {u['id']:<32} [{tags_str}]")
        if len(audit_res["untagged"]) > 15:
            click.echo(f"    ... and {len(audit_res['untagged']) - 15} more (use --json)")

    if apply_changes:
        click.echo(
            f"\n✓ Successfully applied hygiene updates: {cat_updates} categories updated, {tag_updates} tag sets assigned.\n"
        )
    else:
        click.echo("\nRun with '--apply' to persist these updates non-destructively to metadata.json on disk.\n")


__all__ = ["knowledge_stats", "knowledge_hygiene"]
