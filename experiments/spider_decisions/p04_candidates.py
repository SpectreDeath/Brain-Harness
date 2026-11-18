"""Phase 4.1 (Blind): Extract unlearned arXiv+tested grm candidates alphabetically for human selection."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import SNAPSHOTS, bootstrap, project_entities, query, write_md  # noqa: E402

bootstrap()


def main() -> int:
    from ontology_spider.api import load_model

    model = load_model(SNAPSHOTS / "grm.json")
    q_str = (
        "query recommend research_project "
        "[has_tests=true, has_arxiv=true, harness_learned=false, is_generic_unit=false]"
    )
    res = query(model, q_str)
    candidate_ids = sorted({str(ans["value"]) for ans in (res.get("answers") or [])})
    ents = project_entities(model)

    rows: list[dict[str, Any]] = []
    for uid in candidate_ids:
        attrs = dict(ents.get(uid) or {})
        rows.append(
            {
                "unit_id": uid,
                "domain": str(attrs.get("domain_class") or ""),
                "framework": str(attrs.get("primary_framework") or "none"),
                "test_count": int(attrs.get("test_file_count") or 0),
                "py_file_count": int(attrs.get("py_file_count") or 0),
                "has_arxiv": bool(attrs.get("has_arxiv")),
            }
        )

    md_lines = [
        "# Phase 4 — Candidate Research Projects for Human Pick-5 (Blind List)",
        "",
        f"Source: `grm` snapshot (`{len(rows)}` unlearned subprojects matching "
        "`has_tests=true, has_arxiv=true, harness_learned=false, is_generic_unit=false`), "
        "sorted **alphabetically** (no ranking scores computed or shown).",
        "",
        "Pick **5** `unit_id` values you would learn next.",
        "",
        "| # | unit_id | domain | framework | test_count | py_file_count | arXiv |",
        "|---:|---|---|---|---:|---:|---|",
    ]
    for idx, r in enumerate(rows, start=1):
        ax = "yes" if r["has_arxiv"] else "no"
        md_lines.append(
            f"| {idx} | `{r['unit_id']}` | `{r['domain']}` | {r['framework']} "
            f"| {r['test_count']} | {r['py_file_count']} | {ax} |"
        )
    md_lines.append("")
    md_path = write_md(4, "candidates_for_human", "\n".join(md_lines))
    print(f"Candidates written ({len(rows)}): {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
