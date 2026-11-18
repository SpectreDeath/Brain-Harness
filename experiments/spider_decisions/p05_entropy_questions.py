"""Phase 5: Compare entropy-driven attribute questioning vs random order on top-20 targets."""

from __future__ import annotations

import json
from pathlib import Path
import random
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import RESULTS, SNAPSHOTS, bootstrap, write_json, write_md  # noqa: E402

bootstrap()

EXCLUDED_ATTRS = frozenset({"raw_name", "learned_ki_id"})
_MISSING = object()


def _simulate_target(
    model: Any,
    target_id: str,
    candidate_ids: list[str],
    *,
    policy: str,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    from ontology_spider.api import rank_discriminating_attributes

    remaining = list(candidate_ids)
    asked: list[dict[str, Any]] = []
    asked_names: set[str] = set()

    while len(remaining) > 1:
        ranks = rank_discriminating_attributes(model, remaining)
        eligible = [
            r
            for r in ranks
            if not r.get("is_identifier_like")
            and r.get("attribute") not in EXCLUDED_ATTRS
            and r.get("attribute") not in asked_names
            and int(r.get("distinct_values") or 0) > 1
            and float(r.get("classification_score") or 0.0) > 0.0
        ]
        if not eligible:
            break

        if policy == "entropy":
            chosen = max(
                eligible,
                key=lambda r: (float(r["classification_score"]), str(r["attribute"])),
            )
        elif policy == "random":
            assert rng is not None
            chosen = rng.choice(eligible)
        else:
            raise ValueError(f"Unknown policy: {policy}")

        attr = str(chosen["attribute"])
        asked_names.add(attr)
        target_val = model.entities[target_id].attributes.get(attr, _MISSING)
        remaining = [cid for cid in remaining if model.entities[cid].attributes.get(attr, _MISSING) == target_val]
        asked.append(
            {
                "step": len(asked) + 1,
                "attribute": attr,
                "value": None if target_val is _MISSING else target_val,
                "classification_score": round(float(chosen["classification_score"]), 4),
                "remaining_count": len(remaining),
            }
        )

    return {
        "target_id": target_id,
        "questions_asked": len(asked),
        "uniquely_identified": len(remaining) == 1,
        "final_remaining_count": len(remaining),
        "final_remaining_ids": remaining,
        "trace": asked,
    }


def _summarize_policy(runs: list[dict[str, Any]]) -> dict[str, Any]:
    counts = [int(r["questions_asked"]) for r in runs]
    unique_count = sum(1 for r in runs if r["uniquely_identified"])
    n = len(runs)
    return {
        "targets": n,
        "mean_questions": round(sum(counts) / n, 4) if n else 0.0,
        "max_questions": max(counts) if counts else 0,
        "min_questions": min(counts) if counts else 0,
        "uniquely_identified_count": unique_count,
        "pct_uniquely_identified": round(100.0 * unique_count / n, 2) if n else 0.0,
    }


def main() -> int:
    from ontology_spider.api import load_model

    ranked_data = json.loads((RESULTS / "p04" / "ranked_targets.json").read_text(encoding="utf-8"))
    top20 = [r["unit_id"] for r in ranked_data["all_candidates"][:20]]
    model = load_model(SNAPSHOTS / "grm.json")

    entropy_runs: list[dict[str, Any]] = []
    random_runs: list[dict[str, Any]] = []

    for idx, uid in enumerate(top20):
        entropy_runs.append(_simulate_target(model, uid, top20, policy="entropy"))
        random_runs.append(_simulate_target(model, uid, top20, policy="random", rng=random.Random(20261118 + idx)))

    entropy_stats = _summarize_policy(entropy_runs)
    random_stats = _summarize_policy(random_runs)

    payload = {
        "candidate_pool": top20,
        "entropy_summary": entropy_stats,
        "random_summary": random_stats,
        "per_target": [
            {
                "unit_id": uid,
                "entropy_questions": e["questions_asked"],
                "entropy_unique": e["uniquely_identified"],
                "random_questions": r["questions_asked"],
                "random_unique": r["uniquely_identified"],
            }
            for uid, e, r in zip(top20, entropy_runs, random_runs, strict=True)
        ],
        "entropy_runs": entropy_runs,
        "random_runs": random_runs,
    }
    json_path = write_json(5, "results", payload)

    md_lines = [
        "# Phase 5 — Entropy-Driven Question Selection vs Random",
        "",
        f"Simulated hidden-target narrowing across the top **{len(top20)}** candidates from Phase 4.",
        "",
        "## Policy Comparison",
        "",
        "| Policy | Mean Questions | Max Questions | Uniquely Identified |",
        "|---|---:|---:|---:|",
        f"| `entropy` (`classification_score`) | {entropy_stats['mean_questions']:.2f} "
        f"| {entropy_stats['max_questions']} | {entropy_stats['uniquely_identified_count']}/{len(top20)} ({entropy_stats['pct_uniquely_identified']:.1f}%) |",
        f"| `random` (seed `20261118 + i`) | {random_stats['mean_questions']:.2f} "
        f"| {random_stats['max_questions']} | {random_stats['uniquely_identified_count']}/{len(top20)} ({random_stats['pct_uniquely_identified']:.1f}%) |",
        "",
        "## Per-Target Breakdown",
        "",
        "| # | unit_id | Entropy Qs | Entropy Unique | Random Qs | Random Unique |",
        "|---:|---|---:|---|---:|---|",
    ]
    for i, (uid, e, r) in enumerate(zip(top20, entropy_runs, random_runs, strict=True), start=1):
        md_lines.append(
            f"| {i} | `{uid}` | {e['questions_asked']} | {e['uniquely_identified']} "
            f"| {r['questions_asked']} | {r['uniquely_identified']} |"
        )
    md_lines.append("")
    md_path = write_md(5, "summary", "\n".join(md_lines))

    print(
        f"Entropy: mean={entropy_stats['mean_questions']:.2f}, max={entropy_stats['max_questions']}, "
        f"unique={entropy_stats['pct_uniquely_identified']:.1f}%"
    )
    print(
        f"Random:  mean={random_stats['mean_questions']:.2f}, max={random_stats['max_questions']}, "
        f"unique={random_stats['pct_uniquely_identified']:.1f}%"
    )
    print(f"JSON: {json_path}")
    print(f"Summary: {md_path}")
    return 0 if entropy_stats["mean_questions"] <= random_stats["mean_questions"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
