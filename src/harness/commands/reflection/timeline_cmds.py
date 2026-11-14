"""Reflection and Knowledge CLI submodule: timeline_cmds."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import json
import sys

import click

from harness.commands._utils import _run_async
from harness.services.storage import SQLiteStorageService

from .group import knowledge_group


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

        tag_cumulative_counts = defaultdict(int)
        mega_tag_crossings = {}
        target_mega_tags = {"endogenous_memory", "self_reflection"}

        total_retrievals = sum(k.retrieval_count for k in items)
        retrieved_items = [k for k in items if k.retrieval_count > 0]
        retrieval_weekly_counts = defaultdict(int)
        for k in retrieved_items:
            if k.last_retrieved_at:
                dt_str = k.last_retrieved_at[:10]
                try:
                    dt = datetime.fromisoformat(k.last_retrieved_at.replace("Z", "+00:00"))
                    yw = f"{dt.year}-W{dt.isocalendar().week:02d}"
                except Exception:
                    yw = dt_str[:7]
                retrieval_weekly_counts[yw] += k.retrieval_count

        sorted_items = sorted(
            [ki for ki in items if ki.created_at],
            key=lambda x: x.created_at,
        )

        for n_t, ki in enumerate(sorted_items, 1):
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

            for tag in ki.tags:
                tag_cumulative_counts[tag] += 1
                if tag in target_mega_tags and tag not in mega_tag_crossings and n_t >= 10:
                    if (tag_cumulative_counts[tag] / n_t) >= 0.15:
                        mega_tag_crossings[tag] = {
                            "date": dt_str,
                            "ki_id": ki.id,
                            "ratio": tag_cumulative_counts[tag] / n_t,
                            "item_index": n_t,
                        }

        return {
            "total_items": len(items),
            "dated_items": dated_items,
            "weekly_growth": dict(sorted(weekly_counts.items())),
            "domain_emergence": domain_first_seen,
            "mega_tag_crossings": mega_tag_crossings,
            "retrievals": {
                "total_retrievals": total_retrievals,
                "retrieved_items_count": len(retrieved_items),
                "weekly_velocity": dict(sorted(retrieval_weekly_counts.items())),
            },
        }

    data = _run_async(_timeline())
    storage.close()

    if as_json:
        click.echo(json.dumps(data, indent=2))
        return

    click.echo("\n📅 Knowledge Vault Temporal Growth Report")
    click.echo("━" * 70)
    click.echo(f"Total Vault Items:       {data['total_items']}")
    click.echo(
        f"Dated Items:             {data['dated_items']} / {data['total_items']} ({data['dated_items'] / max(1, data['total_items']):.1%})"
    )

    click.echo("\nDomain Emergence Order:")
    for dom, info in sorted(data["domain_emergence"].items(), key=lambda x: x[1]["date"]):
        click.echo(f"  • {info['date']}  {dom:<30} (First: {info['first_ki']})")

    click.echo("\nWeekly Creation Velocity:")
    cum = 0
    for yw, cnt in data["weekly_growth"].items():
        cum += cnt
        bar = "█" * min(30, cnt)
        click.echo(f"  • {yw}: {cnt:>3} items {bar:<30} (Cumulative: {cum})")

    if data.get("mega_tag_crossings"):
        click.echo("\nMega-Tag 15% Threshold Crossings:")
        for tag, info in sorted(data["mega_tag_crossings"].items()):
            click.echo(
                f"  • {tag:<22} crossed on {info['date']} (at #{info['item_index']}: {info['ki_id']}, {info['ratio']:.1%})"
            )

    ret = data.get("retrievals", {})
    click.echo("\nRetrieval Velocity:")
    click.echo(
        f"  • Total Retrievals:    {ret.get('total_retrievals', 0)} across {ret.get('retrieved_items_count', 0)} item(s)"
    )
    if ret.get("weekly_velocity"):
        for yw, cnt in ret["weekly_velocity"].items():
            click.echo(f"    - {yw}: {cnt} retrieval(s)")
    click.echo()


__all__ = ["knowledge_timeline"]
