"""Reflection and Knowledge CLI submodule: lifecycle_cmds."""

from __future__ import annotations

import click

from harness.commands._utils import _run_async
from harness.services.storage import SQLiteStorageService

from .group import knowledge_group


@knowledge_group.command("lifecycle")
@click.option("--vault", "-v", "vault_dir", default=".harness/knowledge", help="Path to knowledge vault root directory")
@click.option("--min-retrievals", default=5, type=int, help="Minimum retrievals before evaluating promote/demote")
@click.option("--promote-ratio", default=0.75, type=float, help="Success ratio threshold for promotion")
@click.option("--demote-ratio", default=0.25, type=float, help="Success ratio threshold for demotion")
@click.option(
    "--show-contradictions/--no-show-contradictions",
    default=True,
    help="Display contradiction queue alongside lifecycle audit",
)
@click.option(
    "--apply-contradictions",
    is_flag=True,
    default=False,
    help="Apply contradiction/supersession resolutions to on-disk vault",
)
@click.option(
    "--yes", "-y", is_flag=True, default=False, help="Skip confirmation when applying non-automatic resolutions"
)
def knowledge_lifecycle(
    vault_dir: str,
    min_retrievals: int,
    promote_ratio: float,
    demote_ratio: float,
    show_contradictions: bool,
    apply_contradictions: bool,
    yes: bool,
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

    if apply_contradictions and conflicts:
        click.echo(f"\nApplying Contradiction Resolutions ({len(conflicts)} pair(s)):")
        click.echo("─" * 70)
        applied_count = 0
        for item in conflicts:
            is_auto = item.conflict_type == "supersession_candidate" and item.confidence >= 0.90
            prompt_msg = f"Apply '{item.suggested_edge}' resolution between {item.ki_a} and {item.ki_b}?"
            if is_auto or yes or click.confirm(prompt_msg, default=True):

                async def _apply_one(c=item):
                    item_a = await storage.get_knowledge_item(c.ki_a)
                    item_b = await storage.get_knowledge_item(c.ki_b)
                    if item_a and item_b:
                        if c.suggested_edge == "supersedes":
                            item_a.add_edge(
                                "supersedes",
                                item_b.id,
                                target_kind="ki",
                                derived=False,
                                confidence=1.0,
                                description=c.reason or "Lifecycle candidate",
                            )
                            item_b.status = "SUPERSEDED"
                            item_b.superseded_by = item_a.id
                            await storage.save_knowledge_item(item_a, vault_dir=vault_dir)
                            await storage.save_knowledge_item(item_b, vault_dir=vault_dir)
                            await storage.export_single_item(item_a, vault_dir=vault_dir)
                            await storage.export_single_item(item_b, vault_dir=vault_dir)
                            return True
                        elif c.suggested_edge == "contradicts":
                            item_a.add_edge(
                                "contradicts",
                                item_b.id,
                                target_kind="ki",
                                derived=False,
                                confidence=1.0,
                                description=c.reason or "Lifecycle candidate",
                            )
                            item_b.add_edge(
                                "contradicts",
                                item_a.id,
                                target_kind="ki",
                                derived=False,
                                confidence=1.0,
                                description=c.reason or "Lifecycle candidate",
                            )
                            item_a.status = "CHALLENGED"
                            item_b.status = "CHALLENGED"
                            await storage.save_knowledge_item(item_a, vault_dir=vault_dir)
                            await storage.save_knowledge_item(item_b, vault_dir=vault_dir)
                            await storage.export_single_item(item_a, vault_dir=vault_dir)
                            await storage.export_single_item(item_b, vault_dir=vault_dir)
                            return True
                    return False

                if _run_async(_apply_one()):
                    applied_count += 1
                    click.echo(f"  ✓ Applied '{item.suggested_edge}': {item.ki_a} → {item.ki_b}")
        click.echo(f"✓ Applied {applied_count} resolution(s) to vault.\n")
    elif show_contradictions and conflicts:
        click.echo(f"\nContradiction Review Queue ({len(conflicts)} flagged pair(s)):")
        click.echo("─" * 70)
        for idx, item in enumerate(conflicts, 1):
            click.echo(f"[{idx}] {item.conflict_type.upper()} (Confidence: {item.confidence:.0%})")
            click.echo(f"    KI A: {item.ki_a} | KI B: {item.ki_b}")
            click.echo(f"    Reason: {item.reason}")
            click.echo(
                f"    Suggested Resolution: harness knowledge resolve {item.ki_a} {item.ki_b} --action {item.suggested_edge}\n"
            )

    storage.close()


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
            item_a.add_edge(
                "supersedes",
                item_b.id,
                target_kind="ki",
                derived=False,
                confidence=1.0,
                description=reason or "Manual resolution",
            )
            item_b.status = "SUPERSEDED"
            item_b.superseded_by = item_a.id
            await storage.save_knowledge_item(item_a, vault_dir=vault_dir)
            await storage.save_knowledge_item(item_b, vault_dir=vault_dir)
            await storage.export_single_item(item_a, vault_dir=vault_dir)
            await storage.export_single_item(item_b, vault_dir=vault_dir)
            return f"✓ Marked '{item_b.id}' SUPERSEDED by '{item_a.id}' with directed 'supersedes' edge."
        elif act == "contradict":
            item_a.add_edge(
                "contradicts",
                item_b.id,
                target_kind="ki",
                derived=False,
                confidence=1.0,
                description=reason or "Manual resolution",
            )
            item_b.add_edge(
                "contradicts",
                item_a.id,
                target_kind="ki",
                derived=False,
                confidence=1.0,
                description=reason or "Manual resolution",
            )
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


__all__ = ["knowledge_lifecycle", "knowledge_resolve"]
