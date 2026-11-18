"""Phase 2.2: Rank unverified KIs by incoming graph centrality (in-degree) and tag count."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import bootstrap, load_vault_model, write_json, write_md  # noqa: E402

bootstrap()


def _escape_md(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def main() -> int:
    model = load_vault_model()
    rows: list[dict[str, Any]] = []

    for eid, ent in model.entities.items():
        attrs = dict(getattr(ent, "attributes", {}) or {})
        if attrs.get("isnad_verified") is not False:
            continue
        incoming = model.get_incoming(eid)
        tags = [str(t) for t in (attrs.get("tags") or []) if str(t).strip()]
        pointing_kis = sorted({a.relation.subject for a in incoming})
        incoming_edges = [
            {"subject": a.relation.subject, "predicate": a.relation.predicate}
            for a in sorted(incoming, key=lambda x: (x.relation.predicate, x.relation.subject))
        ]
        rows.append(
            {
                "id": eid,
                "raw_id": str(attrs.get("raw_id") or eid),
                "title": str(attrs.get("title") or ""),
                "category": str(attrs.get("category") or ""),
                "in_degree": len(incoming),
                "tag_count": len(tags),
                "tags": tags,
                "pointing_kis": pointing_kis,
                "incoming_edges": incoming_edges,
                "isnad_count": int(attrs.get("isnad_count") or 0),
                "verified_isnad_count": int(attrs.get("verified_isnad_count") or 0),
            }
        )

    rows.sort(key=lambda r: (-r["in_degree"], -r["tag_count"], r["id"]))
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank

    json_path = write_json(2, "unverified_priority", rows)

    md_lines = [
        "# Phase 2 — Unverified KI Priority Queue (Top 20)",
        "",
        f"Total unverified KIs in vault (`isnad_verified is False`): **{len(rows)}**",
        "",
        "| Rank | KI ID | In-Degree | Tags | Category | Title | Pointing KIs |",
        "|---:|---|---:|---:|---|---|---|",
    ]
    for row in rows[:20]:
        title = _escape_md(row["title"])[:72]
        pointers = ", ".join(row["pointing_kis"][:5])
        if len(row["pointing_kis"]) > 5:
            pointers += f" (+{len(row['pointing_kis']) - 5} more)"
        md_lines.append(
            f"| {row['rank']} | `{_escape_md(row['id'])}` | {row['in_degree']} "
            f"| {row['tag_count']} | {_escape_md(row['category'])} | {title} | {_escape_md(pointers)} |"
        )
    md_lines.append("")
    md_path = write_md(2, "unverified_priority", "\n".join(md_lines))

    top5 = [f"{r['id']}(in={r['in_degree']},tags={r['tag_count']})" for r in rows[:5]]
    print(f"Unverified KIs ranked: {len(rows)}; Top 5: {top5}")
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
