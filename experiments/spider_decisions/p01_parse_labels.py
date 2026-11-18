"""Phase 1.3: Parse bridges_label_sheet.md into ground truth JSON and before-fix metrics."""

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


def parse_label_sheet(md_path: Path, before_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse T/F annotations from bridges_label_sheet.md and join to before_rows."""
    by_key = {(r["snapshot"], r["raw_name"], r["object"]): r for r in before_rows}
    ground_truth: list[dict[str, Any]] = []
    for line in md_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 7 or not cells[0].isdigit():
            continue
        idx = int(cells[0])
        snap, unit, ki_id, ki_title, draft, final = cells[1:7]
        final_upper = final.upper()
        if final_upper not in ("T", "F"):
            raise ValueError(f"Row {idx} ({snap}/{unit}) missing T/F label: {final!r}")
        base = by_key.get((snap, unit, ki_id), {})
        ground_truth.append(
            {
                "row": idx,
                "snapshot": snap,
                "subject": base.get("subject"),
                "raw_name": unit,
                "object": ki_id,
                "ki_title": ki_title,
                "draft_label": draft,
                "ground_truth": final_upper == "T",
                "label": final_upper,
            }
        )
    return ground_truth


def main() -> int:
    p01_dir = RESULTS / "p01"
    before_rows = json.loads((p01_dir / "bridges_before.json").read_text(encoding="utf-8"))
    gt = parse_label_sheet(p01_dir / "bridges_label_sheet.md", before_rows)
    if len(gt) != len(before_rows):
        raise RuntimeError(f"Expected {len(before_rows)} rows, parsed {len(gt)}")

    total = len(gt)
    tp = sum(1 for r in gt if r["ground_truth"])
    fp = total - tp
    metrics_before = {
        "total_bridges": total,
        "true_positives": tp,
        "false_positives": fp,
        "fp_rate": round(fp / total, 4) if total else 0.0,
        "false_positive_examples": [
            f"{r['snapshot']}/{r['raw_name']} -> {r['object']}" for r in gt if not r["ground_truth"]
        ],
    }
    gt_path = write_json(1, "bridges_ground_truth", gt)
    m_path = write_json(1, "metrics_before", metrics_before)
    print(f"Ground truth saved: {gt_path} ({tp} T, {fp} F)")
    print(f"Metrics before saved: {m_path} -> FP rate = {metrics_before['fp_rate']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
