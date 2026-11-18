"""Phase 8.2-8.3: Parse confirmed ground truth and evaluate rule classifier on repo attributes."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import RESULTS, SNAPSHOTS, bootstrap, project_entities, write_json, write_md  # noqa: E402

bootstrap()

LABELS = ("plugin", "ki_only", "skip")
CHILD_SNAPSHOT_MAP: dict[str, str] = {
    "google-research-master": "grm",
    "gvisor": "gvisor",
    "airllm": "airllm",
    "airllm-plus": "airllm_plus",
}
TIER_RANK = {"large": 3, "medium": 2, "small": 1, "non_python": 0}


def _parse_ground_truth_sheet(sheet_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in sheet_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip().strip("`") for c in s.strip("|").split("|")]
        if len(cells) < 6 or not cells[0].isdigit():
            continue
        portfolio, repo, _draft, _ev, final = cells[1:6]
        if final not in LABELS:
            raise ValueError(f"Invalid label for {repo}: {final!r}")
        rows.append({"portfolio": portfolio, "repo": repo, "label": final})
    return rows


def _pick_dominant_unit(model: Any) -> tuple[str, dict[str, Any]]:
    ents = project_entities(model)
    non_gen = [(eid, dict(a)) for eid, a in ents.items() if not a.get("is_generic_unit")]
    pool = non_gen or [(eid, dict(a)) for eid, a in ents.items()]
    assert pool, "No project entities in model"
    best_eid, best_attrs = max(
        pool,
        key=lambda kv: (
            int(kv[1].get("py_file_count") or 0) + int(kv[1].get("test_file_count") or 0),
            TIER_RANK.get(str(kv[1].get("size_tier") or "non_python"), 0),
            1 if kv[1].get("has_readme") else 0,
            str(kv[1].get("raw_name") or kv[0]),
        ),
    )
    return str(best_attrs.get("raw_name") or best_eid), best_attrs


def _classify_attrs(attrs: dict[str, Any]) -> str:
    primary_language = str(attrs.get("primary_language") or "")
    has_tests = bool(attrs.get("has_tests"))
    packaging = str(attrs.get("packaging") or "none")
    has_readme = bool(attrs.get("has_readme"))
    has_arxiv = bool(attrs.get("has_arxiv"))

    if primary_language == "python" and has_tests and packaging in {"pyproject", "setup_py", "requirements"}:
        return "plugin"
    if has_readme and (has_arxiv or primary_language != "python"):
        return "ki_only"
    return "skip"


def main() -> int:
    from ontology_spider.api import load_model

    p08_dir = RESULTS / "p08"
    gt_rows = _parse_ground_truth_sheet(p08_dir / "ground_truth_sheet.md")
    gt_path = write_json(8, "ground_truth", gt_rows)

    groot_model = load_model(SNAPSHOTS / "google_portfolio_root.json")
    groot_ents = {
        str(attrs.get("raw_name") or eid): dict(attrs) for eid, attrs in project_entities(groot_model).items()
    }
    child_models = {repo: load_model(SNAPSHOTS / f"{snap}.json") for repo, snap in CHILD_SNAPSHOT_MAP.items()}

    cm: dict[str, dict[str, int]] = {t: {p: 0 for p in LABELS} for t in LABELS}
    predictions: list[dict[str, Any]] = []
    correct = 0

    for row in gt_rows:
        repo = row["repo"]
        truth = row["label"]
        if repo in child_models:
            dom_unit, attrs = _pick_dominant_unit(child_models[repo])
            attr_source = f"snapshot:{CHILD_SNAPSHOT_MAP[repo]}"
        else:
            attrs = groot_ents[repo]
            dom_unit = repo
            attr_source = "snapshot:google_portfolio_root"

        pred = _classify_attrs(attrs)
        is_correct = pred == truth
        if is_correct:
            correct += 1
        cm[truth][pred] += 1
        predictions.append(
            {
                "portfolio": row["portfolio"],
                "repo": repo,
                "ground_truth": truth,
                "predicted": pred,
                "correct": is_correct,
                "dominant_unit": dom_unit,
                "attr_source": attr_source,
                "primary_language": attrs.get("primary_language"),
                "packaging": attrs.get("packaging"),
                "has_tests": attrs.get("has_tests"),
                "has_readme": attrs.get("has_readme"),
                "has_arxiv": attrs.get("has_arxiv"),
                "py_file_count": attrs.get("py_file_count"),
            }
        )

    accuracy = round(correct / len(gt_rows), 4) if gt_rows else 0.0
    misclassified = [p for p in predictions if not p["correct"]]

    payload = {
        "total_repos": len(gt_rows),
        "correct": correct,
        "accuracy": accuracy,
        "labels": list(LABELS),
        "confusion_matrix": cm,
        "predictions": predictions,
        "misclassifications": misclassified,
    }
    res_path = write_json(8, "results", payload)

    md_lines = [
        "# Phase 8 — Rule Classifier vs Ground Truth Summary",
        "",
        f"Evaluated **{len(gt_rows)}** repositories: **{correct}/{len(gt_rows)}** correct (**accuracy = {accuracy:.4f}**).",
        "",
        "## 3x3 Confusion Matrix (rows = Ground Truth, cols = Predicted)",
        "",
        "| Ground Truth \\ Predicted | `plugin` | `ki_only` | `skip` |",
        "|---|---:|---:|---:|",
    ]
    for t in LABELS:
        md_lines.append(f"| `{t}` | {cm[t]['plugin']} | {cm[t]['ki_only']} | {cm[t]['skip']} |")

    md_lines.extend(
        [
            "",
            "## Per-Repo Predictions",
            "",
            "| Repo | Truth | Predicted | Match | Dominant Unit | Lang / Pkg / Tests / README / arXiv |",
            "|---|---|---|---|---|---|",
        ]
    )
    for p in predictions:
        feats = (
            f"{p['primary_language']} / {p['packaging']} / tests={p['has_tests']} "
            f"/ readme={p['has_readme']} / arxiv={p['has_arxiv']}"
        )
        mark = "OK" if p["correct"] else "MISS"
        md_lines.append(
            f"| `{p['repo']}` | `{p['ground_truth']}` | `{p['predicted']}` | {mark} "
            f"| `{p['dominant_unit']}` ({p['attr_source']}) | {feats} |"
        )
    md_lines.append("")
    md_path = write_md(8, "summary", "\n".join(md_lines))

    print(f"Ground truth: {gt_path}")
    print(f"Classifier accuracy: {correct}/{len(gt_rows)} = {accuracy:.4f}")
    print(f"Confusion matrix: {cm}")
    print(f"Results: {res_path}")
    print(f"Summary: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
