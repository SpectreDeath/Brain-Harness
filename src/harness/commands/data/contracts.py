"""Data contract validation commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import yaml

from harness.services.data_management import DataManagementEngine


async def validate_contract_cmd(
    contract_path: str,
    data_path: str | None = None,
    dataset_path: str | None = None,
    max_quarantine_ratio: float = 0.05,
    out_path: str | None = None,
) -> dict[str, Any]:
    """Validate data records against an Open Data Contract definition."""
    c_p = Path(contract_path)
    d_path = data_path or dataset_path
    if not d_path:
        raise ValueError("data_path or dataset_path must be provided")
    d_p = Path(d_path)

    contract_def = yaml.safe_load(c_p.read_text(encoding="utf-8")) or {}
    raw_data = yaml.safe_load(d_p.read_text(encoding="utf-8")) or []
    if isinstance(raw_data, dict) and "records" in raw_data:
        raw_data = raw_data["records"]

    engine = DataManagementEngine()
    report = engine.validate_contract(raw_data, contract_def, max_quarantine_ratio=max_quarantine_ratio)

    ret = {
        "valid": report.is_compliant,
        "is_compliant": report.is_compliant,
        "total_records": report.total_records,
        "valid_records": report.valid_records,
        "quarantined_records": report.quarantined_records,
        "violations_count": len(report.violations),
        "contract_name": report.contract_name,
        "version": report.version,
        "violations": [v.to_dict() for v in report.violations],
        "report": report,
    }
    if out_path:
        Path(out_path).write_text(
            json.dumps({k: v for k, v in ret.items() if k != "report"}, indent=2),
            encoding="utf-8",
        )

    return ret
