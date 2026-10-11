"""Data quality profiling commands across the 6 DAMA quality dimensions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import yaml

from harness.services.data_management import DataManagementEngine


async def profile_quality_cmd(
    data_path: str | None = None,
    dataset_path: str | None = None,
    rules_path: str | None = None,
    key_field: str = "id",
    pass_threshold: float = 70.0,
    out_markdown: str | None = None,
    out_json: str | None = None,
) -> dict[str, Any]:
    """Profile data records across the 6 DAMA quality dimensions."""
    d_path = data_path or dataset_path
    if not d_path:
        raise ValueError("data_path or dataset_path must be provided")
    d_p = Path(d_path)

    raw_data = yaml.safe_load(d_p.read_text(encoding="utf-8")) or []
    if isinstance(raw_data, dict) and "records" in raw_data:
        raw_data = raw_data["records"]

    req_fields = None
    keys = [key_field] if key_field != "id" else None
    acc_ranges = None
    if rules_path:
        r_p = Path(rules_path)
        if r_p.exists():
            cfg = yaml.safe_load(r_p.read_text(encoding="utf-8")) or {}
            rules_block = cfg.get("rules", cfg)
            req_fields = rules_block.get("completeness", {}).get("required_fields")
            acc_dict = rules_block.get("accuracy", {}).get("numeric_ranges")
            if acc_dict:
                acc_ranges = {k: (float(v[0]), float(v[1])) for k, v in acc_dict.items()}
            thresh = cfg.get("thresholds", {}).get("overall_min_score")
            if thresh is not None:
                pass_threshold = float(thresh)
            uniq_keys = rules_block.get("uniqueness", {}).get("primary_keys")
            if uniq_keys and not keys:
                keys = list(uniq_keys)
    if not keys:
        keys = [key_field]

    engine = DataManagementEngine()
    scorecard = engine.profile_quality(
        raw_data,
        dataset_name=d_p.stem,
        key_fields=keys,
        required_fields=req_fields,
        accuracy_ranges=acc_ranges,
        pass_threshold=pass_threshold,
    )

    ret = {
        "passed": scorecard.passed,
        "overall_score": scorecard.overall_score,
        "total_records": scorecard.total_records,
        "dimensions": {k: v.to_dict() for k, v in scorecard.dimensions.items()},
        "defects_summary": scorecard.defects_summary,
        "scorecard": scorecard,
    }
    if out_json:
        Path(out_json).write_text(
            json.dumps({k: v for k, v in ret.items() if k != "scorecard"}, indent=2),
            encoding="utf-8",
        )
    if out_markdown:
        Path(out_markdown).write_text(scorecard.generate_markdown(), encoding="utf-8")

    return ret
