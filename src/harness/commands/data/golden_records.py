"""Golden record entity resolution commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import yaml

from harness.services.data_management import DataManagementEngine, EntityRecord


async def resolve_golden_records_cmd(
    data_path: str | None = None,
    dataset_path: str | None = None,
    match_keys: str | list[str] | None = None,
    source_priority: str | list[str] | None = None,
    sources: str | list[str] | None = None,
    out_path: str | None = None,
) -> dict[str, Any]:
    """Cluster multi-source feeds and resolve canonical Golden Records."""
    d_path = data_path or dataset_path
    if not d_path:
        raise ValueError("data_path or dataset_path must be provided")
    d_p = Path(d_path)

    raw_data = yaml.safe_load(d_p.read_text(encoding="utf-8")) or []
    if isinstance(raw_data, dict) and "records" in raw_data:
        raw_data = raw_data["records"]

    if isinstance(match_keys, str):
        match_keys = [k.strip() for k in match_keys.split(",") if k.strip()]
    prios = source_priority or sources
    if isinstance(prios, str):
        prios = [s.strip() for s in prios.split(",") if s.strip()]

    records = [
        EntityRecord(
            record_id=r.get("record_id") or r.get("student_id") or f"rec_{i}",
            source_system=r.get("source_system", "unknown"),
            updated_at=r.get("updated_at", "2026-01-01T00:00:00Z"),
            attributes=r.get("attributes", r),
        )
        for i, r in enumerate(raw_data)
    ]

    engine = DataManagementEngine()
    golden_records = engine.resolve_golden_records(
        records,
        match_keys=match_keys or ["student_id", "national_id", "id"],
        source_priority=prios or ["registrar_system", "mobility_portal", "crm"],
    )

    ret = {
        "golden_records": [g.to_dict() for g in golden_records],
        "input_records": len(raw_data),
        "golden_records_count": len(golden_records),
    }
    if out_path:
        Path(out_path).write_text(json.dumps(ret, indent=2), encoding="utf-8")

    return ret
