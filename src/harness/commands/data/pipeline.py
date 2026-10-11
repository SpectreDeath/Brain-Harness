"""Medallion pipeline execution commands (Bronze -> Silver -> Gold)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import yaml

from harness.services.data_management import DataManagementEngine, MedallionPipelineConfig


async def run_medallion_pipeline_cmd(
    dataset_path: str | None = None,
    raw_path: str | None = None,
    contract_path: str | None = None,
    quality_path: str | None = None,
    source_system: str | None = None,
    primary_keys: str | list[str] | tuple[str, ...] | None = None,
    key_fields: list[str] | None = None,
    sources: list[str] | None = None,
    out_gold: str | None = None,
    out_quarantine: str | None = None,
) -> dict[str, Any]:
    """Execute end-to-end Medallion pipeline (Bronze -> Silver MDM -> Gold Mart)."""
    d_path = dataset_path or raw_path
    if not d_path:
        raise ValueError("dataset_path or raw_path must be provided")
    raw_data = yaml.safe_load(Path(d_path).read_text(encoding="utf-8")) or []
    if isinstance(raw_data, dict) and "records" in raw_data:
        raw_data = raw_data["records"]

    contract_def = {}
    if contract_path:
        c_p = Path(contract_path)
        if c_p.exists():
            contract_def = yaml.safe_load(c_p.read_text(encoding="utf-8")) or {}

    quality_rules = {}
    if quality_path:
        q_p = Path(quality_path)
        if q_p.exists():
            quality_rules = yaml.safe_load(q_p.read_text(encoding="utf-8")) or {}

    keys = primary_keys or key_fields or ["student_id", "national_id", "id"]
    if isinstance(keys, str):
        keys = [k.strip() for k in keys.split(",") if k.strip()]

    source_prio = sources or ["registrar_system", "mobility_portal", "admissions_crm"]
    if source_system and source_system not in source_prio:
        source_prio = [source_system] + list(source_prio)

    match_k = None
    if primary_keys and "student_id" in primary_keys:
        match_k = ["student_id"]
    if quality_rules:
        uniq_keys = quality_rules.get("rules", {}).get("uniqueness", {}).get("primary_keys")
        if uniq_keys:
            keys = uniq_keys

    config = MedallionPipelineConfig(
        contract_def=contract_def,
        quality_rules=quality_rules,
        key_fields=tuple(keys),
        match_keys=tuple(match_k) if match_k else None,
        source_priority=tuple(source_prio),
    )

    engine = DataManagementEngine()
    result = engine.execute_medallion_pipeline(raw_data, config)

    if out_gold:
        Path(out_gold).write_text(json.dumps(result.gold_marts, indent=2), encoding="utf-8")
    if out_quarantine:
        Path(out_quarantine).write_text(json.dumps(result.quarantined_records, indent=2), encoding="utf-8")

    return result.to_dict()
