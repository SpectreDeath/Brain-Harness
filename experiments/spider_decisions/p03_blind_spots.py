"""Phase 3.2-3.3: Finalize approved domain map and rank domain blind spots via spider queries."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import RESULTS, SNAPSHOTS, VAULT, bootstrap, project_entities, query, write_json, write_md  # noqa: E402
from p03_domain_map_draft import OPT_TAGS, REPO_SNAPSHOTS  # noqa: E402

bootstrap()


def _parse_final_mapping(review_md_path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    in_table = False
    for line in review_md_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("| # | Vault `category`"):
            in_table = True
            continue
        if not in_table:
            continue
        if not stripped.startswith("|"):
            if mapping:
                break
            continue
        cells = [c.strip().strip("`") for c in stripped.strip("|").split("|")]
        if len(cells) >= 6 and cells[0].isdigit():
            vault_cat = cells[1]
            final_dc = cells[5] or cells[3]
            mapping[vault_cat] = final_dc
    return mapping


def _count_vault_kis_by_domain(mapping: dict[str, str]) -> tuple[Counter[str], int]:
    counts: Counter[str] = Counter()
    unmapped = 0
    for meta_path in sorted(VAULT.glob("*/metadata.json")):
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        cat = str(data.get("category") or "").strip() or "(empty)"
        target = mapping.get(cat, "unmapped")
        if target.startswith("conditional:"):
            tags = {str(t).strip().lower() for t in (data.get("tags") or []) if str(t).strip()}
            resolved = "optimization_and_compression_project" if (tags & OPT_TAGS) else "unmapped"
        else:
            resolved = target
        if resolved == "unmapped":
            unmapped += 1
        else:
            counts[resolved] += 1
    return counts, unmapped


def _spider_count(model: Any, query_str: str) -> int:
    res = query(model, query_str)
    answers = res.get("answers") or []
    if not answers:
        return 0
    return int(answers[0]["value"])


def main() -> int:
    from ontology_spider.api import load_model

    p03_dir = RESULTS / "p03"
    mapping = _parse_final_mapping(p03_dir / "domain_map_review.md")
    final_map_path = write_json(3, "domain_map_final", {"category_to_domain_class": mapping})

    vault_counts, unmapped_kis = _count_vault_kis_by_domain(mapping)

    models = {snap: load_model(SNAPSHOTS / f"{snap}.json") for snap in REPO_SNAPSHOTS}
    all_domains: set[str] = set()
    py_ents_by_snap: dict[str, dict[str, Any]] = {}
    for snap, model in models.items():
        ents = project_entities(model)
        py_ents_by_snap[snap] = ents
        for attrs in ents.values():
            all_domains.add(str(attrs.get("domain_class") or "general_ml_project"))

    rows: list[dict[str, Any]] = []
    for dc in sorted(all_domains):
        repo_units = 0
        learned_units = 0
        per_snap: dict[str, dict[str, int]] = {}
        for snap, model in models.items():
            s_units = _spider_count(model, f"query count recommend {dc} [is_generic_unit=false]")
            s_learned = _spider_count(model, f"query count recommend {dc} [harness_learned=true]")

            ents = py_ents_by_snap[snap]
            py_units = sum(
                1 for a in ents.values() if a.get("domain_class") == dc and a.get("is_generic_unit") is False
            )
            py_learned = sum(
                1 for a in ents.values() if a.get("domain_class") == dc and a.get("harness_learned") is True
            )
            assert s_units == py_units, f"Spider vs Python mismatch on {snap}/{dc} units: {s_units} != {py_units}"
            assert s_learned == py_learned, (
                f"Spider vs Python mismatch on {snap}/{dc} learned: {s_learned} != {py_learned}"
            )
            repo_units += s_units
            learned_units += s_learned
            if s_units or s_learned:
                per_snap[snap] = {"repo_units": s_units, "learned_units": s_learned}

        v_kis = int(vault_counts.get(dc, 0))
        gap = round(repo_units / (1 + v_kis), 4)
        rows.append(
            {
                "domain_class": dc,
                "repo_units": repo_units,
                "learned_units": learned_units,
                "unlearned_units": repo_units - learned_units,
                "vault_kis": v_kis,
                "gap_score": gap,
                "learned_pct": round(100.0 * learned_units / repo_units, 2) if repo_units else 0.0,
                "per_snapshot": per_snap,
            }
        )

    rows.sort(key=lambda r: (-r["gap_score"], -r["repo_units"], r["domain_class"]))
    for rank, r in enumerate(rows, start=1):
        r["rank"] = rank

    payload = {
        "snapshots": list(REPO_SNAPSHOTS),
        "unmapped_vault_kis": unmapped_kis,
        "spider_python_parity_verified": True,
        "domains": rows,
    }
    json_path = write_json(3, "blind_spots", payload)

    md_lines = [
        "# Phase 3 — Domain Blind-Spot Ranking",
        "",
        f"Evaluated **{len(rows)}** `domain_class` categories across 5 snapshots (`{', '.join(REPO_SNAPSHOTS)}`). "
        f"Unmapped internal/non-research vault KIs: **{unmapped_kis}**. Spider `count` vs `project_entities()` parity: **PASS**.",
        "",
        "| Rank | Domain Class | Repo Units (non-generic) | Learned Units | Vault KIs | Gap Score | Learned % |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        md_lines.append(
            f"| {r['rank']} | `{r['domain_class']}` | {r['repo_units']} | {r['learned_units']} "
            f"| {r['vault_kis']} | {r['gap_score']:.2f} | {r['learned_pct']:.1f}% |"
        )
    md_lines.append("")
    md_path = write_md(3, "blind_spots", "\n".join(md_lines))

    print(f"Final map: {final_map_path}")
    print(f"Blind spots JSON: {json_path}")
    print(f"Blind spots MD: {md_path}")
    for r in rows[:5]:
        print(
            f"  #{r['rank']} {r['domain_class']}: repo={r['repo_units']}, "
            f"learned={r['learned_units']}, vault={r['vault_kis']}, gap={r['gap_score']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
