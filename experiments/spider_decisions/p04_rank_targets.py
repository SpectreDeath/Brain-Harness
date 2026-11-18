"""Phase 4.2-4.4: Rank unlearned grm targets via composite ontology score vs baselines."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import random
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import RESULTS, SNAPSHOTS, bootstrap, project_entities, query, write_json, write_md  # noqa: E402

bootstrap()


def _minmax_normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    if hi <= lo:
        return [0.0 for _ in values]
    span = hi - lo
    return [(v - lo) / span for v in values]


def _method_metrics(
    picked_ids: list[str],
    by_id: dict[str, dict[str, Any]],
    human_set: set[str],
) -> dict[str, Any]:
    overlap = len(set(picked_ids) & human_set)
    domains = [by_id[u]["domain_class"] for u in picked_ids if u in by_id]
    gap_sum = round(sum(by_id[u]["domain_gap"] for u in picked_ids if u in by_id), 2)
    return {
        "picks": picked_ids,
        "overlap_at_5_with_human": overlap,
        "distinct_domains": len(set(domains)),
        "domains": domains,
        "sum_domain_gap": gap_sum,
    }


def main() -> int:
    from ontology_spider.api import load_model

    blind_spots = json.loads((RESULTS / "p03" / "blind_spots.json").read_text(encoding="utf-8"))
    gap_by_domain = {d["domain_class"]: float(d["gap_score"]) for d in blind_spots["domains"]}
    human_payload = json.loads((RESULTS / "p04" / "human_picks.json").read_text(encoding="utf-8"))
    human_picks = list(human_payload["picks"])
    human_set = set(human_picks)

    model = load_model(SNAPSHOTS / "grm.json")
    q_str = (
        "query recommend research_project "
        "[has_tests=true, has_arxiv=true, harness_learned=false, is_generic_unit=false]"
    )
    res = query(model, q_str)
    candidate_ids = sorted({str(ans["value"]) for ans in (res.get("answers") or [])})
    ents = project_entities(model)

    fan_in_counts: Counter[str] = Counter()
    for asrt in model.assertions.values():
        if asrt.relation.predicate == "depends_on_project":
            fan_in_counts[asrt.relation.object] += 1

    raw_rows: list[dict[str, Any]] = []
    for uid in candidate_ids:
        attrs = dict(ents.get(uid) or {})
        dc = str(attrs.get("domain_class") or "general_ml_project")
        raw_rows.append(
            {
                "unit_id": uid,
                "domain_class": dc,
                "primary_framework": str(attrs.get("primary_framework") or "none"),
                "fan_in": int(fan_in_counts.get(uid, 0)),
                "domain_gap": float(gap_by_domain.get(dc, 0.0)),
                "test_depth": int(attrs.get("test_file_count") or 0),
                "size": int(attrs.get("py_file_count") or 0),
            }
        )

    norm_gap = _minmax_normalize([r["domain_gap"] for r in raw_rows])
    norm_fan = _minmax_normalize([float(r["fan_in"]) for r in raw_rows])
    norm_test = _minmax_normalize([float(r["test_depth"]) for r in raw_rows])
    norm_size = _minmax_normalize([float(r["size"]) for r in raw_rows])

    for i, r in enumerate(raw_rows):
        score = 0.35 * norm_gap[i] + 0.30 * norm_fan[i] + 0.20 * norm_test[i] + 0.15 * norm_size[i]
        r["norm_domain_gap"] = round(norm_gap[i], 4)
        r["norm_fan_in"] = round(norm_fan[i], 4)
        r["norm_test_depth"] = round(norm_test[i], 4)
        r["norm_size"] = round(norm_size[i], 4)
        r["score"] = round(score, 6)

    raw_rows.sort(key=lambda r: (-r["score"], -r["domain_gap"], -r["fan_in"], r["unit_id"]))
    for rank, r in enumerate(raw_rows, start=1):
        r["rank"] = rank

    by_id = {r["unit_id"]: r for r in raw_rows}
    spider_5 = [r["unit_id"] for r in raw_rows[:5]]
    largest_5 = [r["unit_id"] for r in sorted(raw_rows, key=lambda x: (-x["size"], x["unit_id"]))[:5]]
    most_tests_5 = [r["unit_id"] for r in sorted(raw_rows, key=lambda x: (-x["test_depth"], x["unit_id"]))[:5]]
    random_5 = random.Random(20261118).sample(candidate_ids, 5)

    methods = {
        "spider_composite": _method_metrics(spider_5, by_id, human_set),
        "largest_5": _method_metrics(largest_5, by_id, human_set),
        "most_tests_5": _method_metrics(most_tests_5, by_id, human_set),
        "random_5": _method_metrics(random_5, by_id, human_set),
        "human_picks": _method_metrics(human_picks, by_id, human_set),
    }

    ranked_payload = {
        "candidate_count": len(raw_rows),
        "top_5": raw_rows[:5],
        "all_candidates": raw_rows,
        "baselines_and_metrics": methods,
    }
    json_path = write_json(4, "ranked_targets", ranked_payload)

    md_lines = [
        "# Phase 4 — Next-5 Learning Targets Comparison",
        "",
        f"Evaluated **{len(raw_rows)}** `grm` candidates (`has_tests=true, has_arxiv=true, harness_learned=false, is_generic_unit=false`).",
        "",
        "## Spider Composite Top 5",
        "",
        "| Rank | unit_id | Domain | Score | Gap | Fan-In | Tests | Py Files |",
        "|---:|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in raw_rows[:5]:
        md_lines.append(
            f"| {r['rank']} | `{r['unit_id']}` | `{r['domain_class']}` | {r['score']:.4f} "
            f"| {r['domain_gap']:.1f} | {r['fan_in']} | {r['test_depth']} | {r['size']} |"
        )

    md_lines.extend(
        [
            "",
            "## Method Comparison vs Blind Picks",
            "",
            "| Method | Overlap@5 w/ Human | Distinct Domains | Sum `domain_gap` | Picks |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for m_name, m in methods.items():
        picks_str = ", ".join(f"`{p}`" for p in m["picks"])
        md_lines.append(
            f"| `{m_name}` | {m['overlap_at_5_with_human']} | {m['distinct_domains']} "
            f"| {m['sum_domain_gap']:.2f} | {picks_str} |"
        )
    md_lines.append("")
    md_path = write_md(4, "comparison", "\n".join(md_lines))

    print(f"Ranked {len(raw_rows)} candidates -> top_5={spider_5}")
    print(f"Comparison JSON: {json_path}")
    print(f"Comparison MD: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
