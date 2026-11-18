"""Phase 1.7-1.8: Rebuild 5 snapshots post-fix, evaluate FP rate/recall, and verify regression set."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import (  # noqa: E402
    AIRLLM_ROOT,
    GOOGLE_ROOT,
    GRM_ROOT,
    RESULTS,
    bootstrap,
    load_repo_model,
    project_entities,
    write_json,
    write_md,
)

bootstrap()

TARGETS: dict[str, Path] = {
    "google_portfolio_root": GOOGLE_ROOT,
    "grm": GRM_ROOT,
    "gvisor": GOOGLE_ROOT / "gvisor",
    "airllm": AIRLLM_ROOT / "airllm",
    "airllm_plus": AIRLLM_ROOT / "airllm-plus",
}

REGRESSION_SET: tuple[tuple[str, str], ...] = (
    ("google_portfolio_root", "gvisor"),
    ("grm", "latent_programmer"),
    ("grm", "active_selective_prediction"),
    ("grm", "scann"),
    ("grm", "cisc"),
    ("grm", "gfsa"),
    ("grm", "etcmodel"),
    ("grm", "imp"),
    ("grm", "uq_benchmark_2019"),
    ("airllm", "air_llm"),
)


def main() -> int:
    p01_dir = RESULTS / "p01"
    gt_rows = json.loads((p01_dir / "bridges_ground_truth.json").read_text(encoding="utf-8"))
    metrics_before = json.loads((p01_dir / "metrics_before.json").read_text(encoding="utf-8"))

    gt_map = {(r["snapshot"], r["raw_name"], r["object"]): bool(r["ground_truth"]) for r in gt_rows}
    true_before = sum(1 for r in gt_rows if r["ground_truth"])

    models: dict[str, Any] = {}
    after_bridges: list[dict[str, Any]] = []

    for snap_name, repo_path in TARGETS.items():
        model = load_repo_model(repo_path, snap_name, refresh=True)
        models[snap_name] = model
        for asrt in model.assertions.values():
            if asrt.relation.predicate != "bridges_to_harness":
                continue
            subj = asrt.relation.subject
            ki_id = asrt.relation.object
            attrs = dict(getattr(model.entities.get(subj), "attributes", {}) or {})
            raw_name = str(attrs.get("raw_name") or subj)
            key = (snap_name, raw_name, ki_id)
            label = gt_map.get(key)
            after_bridges.append(
                {
                    "snapshot": snap_name,
                    "subject": subj,
                    "raw_name": raw_name,
                    "object": ki_id,
                    "match_strength": attrs.get("learned_match_strength"),
                    "ground_truth": label,
                }
            )

    total_after = len(after_bridges)
    tp_after = sum(1 for r in after_bridges if r["ground_truth"] is True)
    fp_after_exact = sum(1 for r in after_bridges if r["ground_truth"] is False)
    swapped_bridges = [r for r in after_bridges if r["ground_truth"] is None]
    # Swapped bridges for units not previously labeled TP are counted as FPs honestly
    tp_unit_pairs = {(r["snapshot"], r["raw_name"]) for r in gt_rows if r["ground_truth"]}
    unknown_fps = [r for r in swapped_bridges if (r["snapshot"], r["raw_name"]) not in tp_unit_pairs]
    fp_after = fp_after_exact + len(unknown_fps)
    fp_rate_after = round(fp_after / total_after, 4) if total_after else 0.0
    true_recall = round(tp_after / true_before, 4) if true_before else 1.0

    # Check known false bridges gone
    after_pairs = {(r["snapshot"], r["raw_name"]) for r in after_bridges}
    runtime_gone = ("airllm_plus", "runtime") not in after_pairs
    rpc_gone = ("grm", "rpc") not in after_pairs

    # Dropped bridges breakdown
    after_keys = {(r["snapshot"], r["raw_name"], r["object"]) for r in after_bridges}
    removed_fps: list[str] = []
    removed_tps: list[str] = []
    remaining_fps: list[str] = []
    for r in gt_rows:
        k = (r["snapshot"], r["raw_name"], r["object"])
        tag = f"{r['snapshot']}/{r['raw_name']} -> {r['object']}"
        if k not in after_keys:
            if r["ground_truth"]:
                removed_tps.append(tag)
            elif (r["snapshot"], r["raw_name"]) not in after_pairs:
                removed_fps.append(tag)
        elif not r["ground_truth"]:
            remaining_fps.append(tag)
    for r in unknown_fps:
        remaining_fps.append(f"{r['snapshot']}/{r['raw_name']} -> {r['object']} (swapped KI)")

    # Step 1.8 Regression set check
    reg_results: list[dict[str, Any]] = []
    for snap_name, unit_name in REGRESSION_SET:
        p_ents = project_entities(models[snap_name])
        matched_attrs = None
        for attrs in p_ents.values():
            if attrs.get("raw_name") == unit_name:
                matched_attrs = dict(attrs)
                break
        passed = bool(matched_attrs and matched_attrs.get("harness_learned") is True)
        reg_results.append(
            {
                "snapshot": snap_name,
                "unit": unit_name,
                "passed": passed,
                "learned_ki_id": (matched_attrs or {}).get("learned_ki_id", ""),
                "strength": (matched_attrs or {}).get("learned_match_strength", "none"),
            }
        )

    all_reg_passed = all(r["passed"] for r in reg_results)
    metrics_after = {
        "total_bridges": total_after,
        "true_positives": tp_after,
        "false_positives": fp_after,
        "unknown_new_bridges": len(swapped_bridges),
        "fp_rate": fp_rate_after,
        "true_bridge_recall": true_recall,
        "known_false_bridges_gone": {"airllm_plus/runtime": runtime_gone, "grm/rpc": rpc_gone},
        "removed_false_positives": removed_fps,
        "removed_true_positives": removed_tps,
        "remaining_false_positives": remaining_fps,
        "regression_all_passed": all_reg_passed,
        "regression_results": reg_results,
    }
    write_json(1, "bridges_after", after_bridges)
    m_path = write_json(1, "metrics_after", metrics_after)

    md_lines = [
        "# Phase 1 — False-Bridge Audit & Fix Summary",
        "",
        "## Before vs After Metrics",
        "",
        "| Metric | Before Fix | After Fix |",
        "|---|---:|---:|",
        f"| Total bridges | {metrics_before['total_bridges']} | {total_after} |",
        f"| True positives | {metrics_before['true_positives']} | {tp_after} |",
        f"| False positives | {metrics_before['false_positives']} | {fp_after} |",
        f"| FP rate | {metrics_before['fp_rate']:.4f} | {fp_rate_after:.4f} |",
        f"| True-bridge recall | 1.0000 | {true_recall:.4f} |",
        f"| `airllm_plus/runtime` gone | False | {runtime_gone} |",
        f"| `grm/rpc` gone | False | {rpc_gone} |",
        "",
        "## Bridge Changes",
        f"- **Removed FPs ({len(removed_fps)}):** {', '.join(removed_fps) or 'none'}",
        f"- **Removed TPs ({len(removed_tps)}):** {', '.join(removed_tps) or 'none'}",
        f"- **Remaining FPs ({len(remaining_fps)}):** {', '.join(remaining_fps) or 'none'}",
        "",
        "## Regression Set Verification (Step 1.8)",
        "",
        "| Snapshot | Unit | Status | Match Strength | Learned KI ID |",
        "|---|---|---|---|---|",
    ]
    for r in reg_results:
        status = "PASS" if r["passed"] else "FAIL"
        md_lines.append(f"| {r['snapshot']} | {r['unit']} | {status} | {r['strength']} | `{r['learned_ki_id']}` |")
    md_lines.append("")
    s_path = write_md(1, "summary", "\n".join(md_lines))

    print(
        f"After: total={total_after}, TP={tp_after}, FP={fp_after}, "
        f"FP_rate={fp_rate_after:.4f}, recall={true_recall:.4f}, "
        f"reg_passed={all_reg_passed}, runtime_gone={runtime_gone}, rpc_gone={rpc_gone}"
    )
    print(f"Metrics: {m_path}")
    print(f"Summary: {s_path}")

    acceptance = (
        runtime_gone
        and rpc_gone
        and fp_rate_after < metrics_before["fp_rate"]
        and true_recall >= 0.95
        and all_reg_passed
    )
    return 0 if acceptance else 1


if __name__ == "__main__":
    raise SystemExit(main())
