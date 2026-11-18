"""Phase 4.1 (Blind): Partition unlearned arXiv+tested grm candidates into 5 alphabetical domain shortlists."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import random
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import SNAPSHOTS, bootstrap, project_entities, query, write_json, write_md  # noqa: E402

bootstrap()

SHORTLIST_SEED = 2026111841
SHORTLIST_SIZE = 8
NUM_SHORTLISTS = 5


def main() -> int:
    from ontology_spider.api import load_model

    model = load_model(SNAPSHOTS / "grm.json")
    q_str = (
        "query recommend research_project "
        "[has_tests=true, has_arxiv=true, harness_learned=false, is_generic_unit=false]"
    )
    res = query(model, q_str)
    candidate_ids = sorted({str(ans["value"]) for ans in (res.get("answers") or [])})
    assert len(candidate_ids) == 127, f"Expected 127 candidates, found {len(candidate_ids)}"
    ents = project_entities(model)

    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for uid in candidate_ids:
        attrs = dict(ents.get(uid) or {})
        domain = str(attrs.get("domain_class") or "")
        by_domain[domain].append(
            {
                "unit_id": uid,
                "domain": domain,
                "framework": str(attrs.get("primary_framework") or "none"),
                "test_count": int(attrs.get("test_file_count") or 0),
                "py_file_count": int(attrs.get("py_file_count") or 0),
                "has_arxiv": bool(attrs.get("has_arxiv")),
            }
        )

    domain_counts = {d: len(by_domain[d]) for d in sorted(by_domain)}
    # Top 5 domains by pool size (tie-break alphabetically), then display domains alphabetically for blindness.
    top_domains_by_size = sorted(by_domain, key=lambda d: (-len(by_domain[d]), d))[:NUM_SHORTLISTS]
    selected_domains = sorted(top_domains_by_size)

    rng = random.Random(SHORTLIST_SEED)
    shortlists: list[dict[str, Any]] = []
    for domain in selected_domains:
        pool = sorted(by_domain[domain], key=lambda r: r["unit_id"])
        assert len(pool) >= SHORTLIST_SIZE, f"Domain {domain} has only {len(pool)} < {SHORTLIST_SIZE}"
        k = min(SHORTLIST_SIZE, len(pool))
        sampled = sorted(rng.sample(pool, k), key=lambda r: r["unit_id"])
        assert 1 <= len(sampled) <= SHORTLIST_SIZE
        shortlists.append(
            {
                "domain": domain,
                "pool_size": len(pool),
                "forced_pick": len(sampled) == 1,
                "candidates": sampled,
            }
        )

    md_lines = [
        "# Phase 4 — Blind Domain Shortlists for Human Pick-5",
        "",
        f"Source: `grm` snapshot (`{len(candidate_ids)}` unlearned subprojects matching "
        "`has_tests=true, has_arxiv=true, harness_learned=false, is_generic_unit=false`).",
        f"Partitioned into **{len(shortlists)}** domain shortlists (up to `{SHORTLIST_SIZE}` candidates per domain, "
        f"seed `{SHORTLIST_SEED}`), domains and rows sorted **alphabetically** (no scores computed or shown).",
        "",
        "Pick **1** `unit_id` from each shortlist (**5 picks total**).",
        "",
    ]

    for idx, sl in enumerate(shortlists, start=1):
        md_lines.extend(
            [
                f"## Shortlist {idx} — `{sl['domain']}`",
                "",
                "| # | unit_id | framework | test_count | py_file_count | arXiv |",
                "|---:|---|---|---:|---:|---|",
            ]
        )
        for row_idx, r in enumerate(sl["candidates"], start=1):
            ax = "yes" if r["has_arxiv"] else "no"
            md_lines.append(
                f"| {row_idx} | `{r['unit_id']}` | {r['framework']} | {r['test_count']} | {r['py_file_count']} | {ax} |"
            )
        md_lines.append("")

    md_path = write_md(4, "candidates_for_human", "\n".join(md_lines))
    meta_path = write_json(
        4,
        "shortlists_meta",
        {
            "seed": SHORTLIST_SEED,
            "shortlist_size": SHORTLIST_SIZE,
            "total_candidates": len(candidate_ids),
            "domain_counts": domain_counts,
            "shortlists": shortlists,
        },
    )
    print(f"Candidates written ({len(candidate_ids)} total -> {len(shortlists)} shortlists): {md_path}")
    print(f"Shortlists metadata: {meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
