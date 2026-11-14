"""Reflection and Knowledge CLI submodule: vault_cmds."""

from __future__ import annotations

from pathlib import Path
import json
import sys

import click

from harness.commands._utils import _run_async
from harness.services.storage import SQLiteStorageService

from .group import knowledge_group


@knowledge_group.command("sync")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option(
    "--db", "db_path", default=None, help="Path to SQLite storage database (defaults to ~/.harness/storage.db)"
)
@click.option("--strict", is_flag=True, default=False, help="Fail with exit code 1 if any vault items fail validation")
def knowledge_sync(vault_dir: str, db_path: str | None, strict: bool) -> None:
    """Sync all on-disk Knowledge Items from .harness/knowledge/ into the storage database."""
    storage_path = db_path or (Path.home() / ".harness" / "storage.db")
    storage = SQLiteStorageService(storage_path)

    async def _sync():
        try:
            count = await storage.sync_knowledge_vault(vault_dir, strict=strict)
            skipped = storage.get_last_skipped_items()
            return count, skipped, None
        except Exception as e:
            return 0, [], str(e)

    synced, skipped, err = _run_async(_sync())
    storage.close()

    if err:
        click.echo(f"✗ Sync failed: {err}", err=True)
        sys.exit(1)

    if skipped:
        click.echo(f"⚠ Warning: {len(skipped)} item(s) skipped during sync:")
        for name, reason in skipped:
            click.echo(f"  • {name}: {reason}")

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


@knowledge_group.command("joint-query")
@click.argument("topic")
@click.option("--limit", "-l", default=5, help="Maximum items to return per graph")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option("--skills-root", default=".", help="Root directory for skills discovery")
@click.option("--json", "json_output", is_flag=True, help="Emit raw JSON payload")
def knowledge_joint_query(topic: str, limit: int, vault_dir: str, skills_root: str, json_output: bool) -> None:
    """Execute unified dual-graph query across Knowledge Vault and Skill Graph."""
    from harness.services.skill_graph.joint_query import query_knowledge_and_skills

    res = query_knowledge_and_skills(topic, vault_dir=vault_dir, root_path=skills_root, limit=limit)
    if json_output:
        click.echo(json.dumps(res, indent=2))
        return

    click.secho(f"\nDual-Graph Joint Query: '{topic}'", fg="cyan", bold=True)
    click.echo("━" * 76)
    click.echo(f"  Knowledge Vault Items : {res['knowledge_items_count']}")
    click.echo(f"  Matched Skills        : {res['skills_count']}")
    click.echo(f"  Linked Lineage Pairs  : {res['linked_pairs_count']}")

    if res["knowledge_items"]:
        click.secho("\n  [KNOWLEDGE VAULT ITEMS]", fg="yellow", bold=True)
        for ki in res["knowledge_items"]:
            click.echo(f"    • [{ki['status']}] {ki['ki_id']}: {ki['title']} ({ki['domain']})")

    if res["skills"]:
        click.secho("\n  [MATCHED AGENT SKILLS]", fg="green", bold=True)
        for sk in res["skills"]:
            chain_str = f" -> {' -> '.join(sk['recommended_chain'])}" if sk["recommended_chain"] else ""
            click.echo(f"    • {sk['skill_name']} (Cluster: {sk['cluster']}, Conf: {sk['confidence']:.2f}){chain_str}")

    if res["linked_pairs"]:
        click.secho("\n  [CROSS-GRAPH LINEAGE LINKS]", fg="magenta", bold=True)
        for lp in res["linked_pairs"]:
            click.echo(f"    • {lp['ki_id']} ──[{lp['relationship']}]──> {lp['skill_name']}")

    if res["unbridged_kis"]:
        click.secho(f"\n  [UNBRIDGED KIs] ({len(res['unbridged_kis'])} items without procedural skills):", fg="red")
        for ub in res["unbridged_kis"][:3]:
            click.echo(f"    • {ub['ki_id']}: {ub['title']}")

    if res["ungrounded_skills"]:
        click.secho(
            f"\n  [UNGROUNDED SKILLS] ({len(res['ungrounded_skills'])} skills without backing Vault KI):", fg="blue"
        )
        for ug in res["ungrounded_skills"][:3]:
            click.echo(f"    • {ug['skill_name']}")
    click.echo("━" * 76)


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
        click.echo(f'Claim: "{claim.get("assertion")}"')
        for node in claim.get("nodes", []):
            mark = "  ✓" if node.get("file_exists") else "  ✗"
            click.echo(f"  {mark} {node.get('uri')} -> exists: {node.get('file_exists')}")
    click.echo()


__all__ = ["knowledge_sync", "knowledge_list", "knowledge_query", "knowledge_joint_query", "knowledge_verify"]
