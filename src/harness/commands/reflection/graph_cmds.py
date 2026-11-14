"""Reflection and Knowledge CLI submodule: graph_cmds."""

from __future__ import annotations

import json
import sys

import click

from harness.commands._utils import _run_async
from harness.services.storage import (
    SQLiteStorageService,
    resolve_knowledge_graph_service,
)

from .group import knowledge_group


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
@click.option(
    "--engine",
    type=click.Choice(["bfs", "sqlite"], case_sensitive=False),
    default="bfs",
    help="Pathfinding engine (bfs or sqlite recursive CTE)",
)
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
def knowledge_path(
    from_id: str, to_id: str, max_depth: int, exclude_derived: bool, directed: bool, engine: str, vault_dir: str
) -> None:
    """Find the BFS shortest path between two graph entities (Rule 55: zero synthetic edges)."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    storage = SQLiteStorageService(":memory:")

    async def _path():
        await storage.sync_knowledge_vault(vault_dir)
        if engine.lower() == "sqlite":
            return storage.find_path_sql(
                from_id,
                to_id,
                max_depth=max_depth,
                exclude_derived=exclude_derived,
                directed=directed,
            )
        items = await storage.list_knowledge_items()
        graph_svc = resolve_knowledge_graph_service()
        graph = graph_svc.derive_graph(items)
        return graph_svc.find_path(
            from_id,
            to_id,
            graph,
            max_depth=max_depth,
            exclude_derived=exclude_derived,
            directed=directed,
        )

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
            click.echo(
                f"  [{idx}] {h['from']} {dir_arrow} [{h['edge_type']}] {dir_arrow} {h['to']} {der} ({h['confidence']:.0%})"
            )
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
@click.option(
    "--transitive", is_flag=True, default=False, help="Traverse multi-hop inbound dependents using SQLite recursive CTE"
)
@click.option("--max-depth", default=6, type=int, help="Maximum search hops when --transitive is set (default: 6)")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
def knowledge_dependents(node_id: str, transitive: bool, max_depth: int, vault_dir: str) -> None:
    """List inbound dependents pointing to a specific Knowledge Item, skill, or code path."""
    storage = SQLiteStorageService(":memory:")

    async def _dependents():
        await storage.sync_knowledge_vault(vault_dir)
        if transitive:
            return storage.get_transitive_dependents_sql(node_id, max_depth=max_depth)
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
            der = "[derived]" if d.get("derived") else "[asserted]"
            depth_str = f" (hop {d['depth']})" if "depth" in d else ""
            click.echo(f"  • {d['source_ki']:<25} ──[{d['edge_type']}]──>{depth_str} {der} ({d['confidence']:.0%})")
    click.echo()


@knowledge_group.command("orphans")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option(
    "--include-single-tag-edges", is_flag=True, default=False, help="Include 1-shared-tag derived same_domain edges"
)
@click.option("--include-shared-source", is_flag=True, default=False, help="Include shared_source derived edges")
@click.option("--max-tag-freq", default=0.15, type=float, help="Tag frequency threshold for mega-tag exclusion")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output orphan diagnostics in JSON format")
def knowledge_orphans(
    vault_dir: str,
    include_single_tag_edges: bool,
    include_shared_source: bool,
    max_tag_freq: float,
    as_json: bool,
) -> None:
    """Identify isolated Knowledge Items and report missing-field triage profiles."""
    storage = SQLiteStorageService(":memory:")

    async def _orphans():
        await storage.sync_knowledge_vault(vault_dir)
        items = await storage.list_knowledge_items()
        graph_svc = resolve_knowledge_graph_service()
        graph = graph_svc.derive_graph(
            items,
            include_single_tag_edges=include_single_tag_edges,
            include_shared_source=include_shared_source,
            max_tag_freq=max_tag_freq,
        )
        return graph_svc.get_orphans(graph, items)

    orphans = _run_async(_orphans())
    storage.close()

    if as_json:
        click.echo(json.dumps(orphans, indent=2))
        return

    click.echo(f"\n🔍 Knowledge Vault Isolated Entity Triage ({orphans['isolated_count']} items)\n" + "━" * 70)
    prof = orphans["profiles"]
    click.echo(
        f"Missing-Field Profile: {prof['untagged']} untagged, {prof['uncategorized']} uncategorized, {prof['missing_source']} missing source\n"
    )
    for item in orphans["isolated_items"][:25]:
        cat = item["category"] or "uncategorized"
        src = "src✓" if item["has_source"] else "no-src"
        click.echo(f"  • {item['id']:<26} [{cat:<24}] ({item['tags_count']} tags, {src}) {item['title'][:40]}")
    if orphans["isolated_count"] > 25:
        click.echo(f"\n  ... and {orphans['isolated_count'] - 25} more (use --json for full list)")
    click.echo()


__all__ = ["knowledge_neighbors", "knowledge_path", "knowledge_topic", "knowledge_dependents", "knowledge_orphans"]
