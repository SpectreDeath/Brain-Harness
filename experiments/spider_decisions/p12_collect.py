"""Phase 12.1: Collect headline metrics from all Phase 0-11 JSON artifacts."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

_EXP_DIR = Path(__file__).resolve().parent
if str(_EXP_DIR) not in sys.path:
    sys.path.insert(0, str(_EXP_DIR))

from common import RESULTS, bootstrap, write_json  # noqa: E402

bootstrap()


def _load_json(phase: int, name: str) -> Any:
    p = RESULTS / f"p{phase:02d}" / f"{name}.json"
    assert p.is_file(), f"Missing artifact: {p}"
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    p00_manifest = _load_json(0, "snapshot_manifest")
    p00_rt = _load_json(0, "roundtrip_check")
    p01_before = _load_json(1, "metrics_before")
    p01_after = _load_json(1, "metrics_after")
    p02_unv = _load_json(2, "unverified_priority")
    p02_dups = _load_json(2, "duplicate_candidates")
    p03_bs = _load_json(3, "blind_spots")
    p04_rt = _load_json(4, "ranked_targets")
    p05_res = _load_json(5, "results")
    p06_m = _load_json(6, "metrics")
    p07_ms = _load_json(7, "memo_scores")
    p08_res = _load_json(8, "results")
    p09_ro = _load_json(9, "refactor_order")
    p10_res = _load_json(10, "results")
    p11_res = _load_json(11, "results")

    summary = {
        "phase_0": {
            "snapshots_count": len(p00_manifest),
            "roundtrip_all_passed": bool(p00_rt.get("all_passed")),
            "vault_entities": p00_manifest["vault"]["entities"],
            "vault_assertions": p00_manifest["vault"]["assertions"],
            "grm_entities": p00_manifest["grm"]["entities"],
            "grm_assertions": p00_manifest["grm"]["assertions"],
        },
        "phase_1": {
            "bridges_before": p01_before["total_bridges"],
            "fp_before": p01_before["false_positives"],
            "fp_rate_before": p01_before["fp_rate"],
            "bridges_after": p01_after["total_bridges"],
            "tp_after": p01_after["true_positives"],
            "fp_after": p01_after["false_positives"],
            "fp_rate_after": p01_after["fp_rate"],
            "true_bridge_recall": p01_after["true_bridge_recall"],
            "known_false_bridges_gone": p01_after["known_false_bridges_gone"],
            "regression_all_passed": p01_after["regression_all_passed"],
        },
        "phase_2": {
            "unverified_kis_count": len(p02_unv),
            "top5_unverified_ids": [r["id"] for r in p02_unv[:5]],
            "total_kis_scanned": p02_dups["total_kis_scanned"],
            "duplicate_candidates_count": p02_dups["candidate_count"],
            "intentional_siblings_count": p02_dups["intentional_siblings_count"],
        },
        "phase_3": {
            "domain_classes_count": len(p03_bs["domains"]),
            "spider_python_parity": bool(p03_bs["spider_python_parity_verified"]),
            "top3_blind_spots": [
                {
                    "domain": d["domain_class"],
                    "gap_score": d["gap_score"],
                    "repo_units": d["repo_units"],
                    "vault_kis": d["vault_kis"],
                }
                for d in p03_bs["domains"][:3]
            ],
        },
        "phase_4": {
            "candidates_count": p04_rt["candidate_count"],
            "human_selection_mode": p04_rt.get("human_selection_mode", "unknown"),
            "top_5_targets": [r["unit_id"] for r in p04_rt["top_5"]],
            "methods": {
                k: {
                    "overlap_at_5": v["overlap_at_5_with_human"],
                    "distinct_domains": v["distinct_domains"],
                    "sum_domain_gap": v["sum_domain_gap"],
                }
                for k, v in p04_rt["baselines_and_metrics"].items()
            },
        },
        "phase_5": {
            "entropy_summary": p05_res["entropy_summary"],
            "random_summary": p05_res["random_summary"],
        },
        "phase_6": {
            "macro_average": p06_m["macro_average"],
            "sparsity": {
                "unique_gold_kis": p06_m["sparsity"]["unique_gold_kis"],
                "gold_kis_with_zero_references_code": p06_m["sparsity"]["gold_kis_with_zero_references_code"],
                "missing_module_edges_count": p06_m["sparsity"]["missing_module_edges_count"],
            },
        },
        "phase_7": {
            "q1": {
                "distinct_kis_cited": p07_ms["q1"]["distinct_kis_cited"],
                "all_cited_kis_in_vault": p07_ms["q1"]["all_cited_kis_in_vault"],
                "cited_claims_verified": p07_ms["q1"]["cited_claims_verified"],
                "cited_claims_total": p07_ms["q1"]["cited_claims_total"],
                "pct_cited_claims_verified": p07_ms["q1"]["pct_cited_claims_verified"],
                "conflicts_flagged": p07_ms["q1"]["conflicts_flagged"],
            },
            "q2": {
                "distinct_kis_cited": p07_ms["q2"]["distinct_kis_cited"],
                "all_cited_kis_in_vault": p07_ms["q2"]["all_cited_kis_in_vault"],
                "cited_claims_verified": p07_ms["q2"]["cited_claims_verified"],
                "cited_claims_total": p07_ms["q2"]["cited_claims_total"],
                "pct_cited_claims_verified": p07_ms["q2"]["pct_cited_claims_verified"],
                "conflicts_flagged": p07_ms["q2"]["conflicts_flagged"],
            },
        },
        "phase_8": {
            "total_repos": p08_res["total_repos"],
            "correct": p08_res["correct"],
            "accuracy": p08_res["accuracy"],
            "confusion_matrix": p08_res["confusion_matrix"],
        },
        "phase_9": {
            "total_units": p09_ro["total_units"],
            "total_depends_on_edges": p09_ro["total_depends_on_edges"],
            "spider_cycles": p09_ro["spider_cycle_violations"],
            "tarjan_scc_count": len(p09_ro["tarjan_scc_cycles"]),
            "tarjan_scc_sizes": [len(c) for c in p09_ro["tarjan_scc_cycles"]],
            "ordered_units": [r["unit"] for r in p09_ro["refactor_order"]],
            "ki_cross_check_top10_count": len(p09_ro["ki_cross_check_top10"]),
        },
        "phase_10": {
            "task_count": p10_res["task_count"],
            "summary_metrics": p10_res["summary_metrics"],
            "unique_wins": p10_res["unique_wins"],
        },
        "phase_11": p11_res["metrics"],
        "summaries_present": {
            f"p{ph:02d}": (RESULTS / f"p{ph:02d}" / "summary.md").is_file() for ph in (1, 4, 5, 6, 8, 9, 10, 11)
        },
    }

    out = write_json(12, "headline_metrics", summary)
    print(f"Collected Phase 0-11 headline metrics: {out}")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
