"""Reflection and Knowledge CLI submodule: lineage_cmds."""

from __future__ import annotations

import click

from harness.commands._utils import _run_async
from harness.services.storage import SQLiteStorageService

from .group import knowledge_group


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
        click.echo(f'          Claim: "{item.assertion_a[:80]}"')
        click.echo(f"    KI B: {item.ki_b} ('{item.title_b[:50]}')")
        click.echo(f'          Claim: "{item.assertion_b[:80]}"')
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


__all__ = ["knowledge_contradictions", "knowledge_lineage"]
