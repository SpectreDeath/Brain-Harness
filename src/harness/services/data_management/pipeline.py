"""Medallion Lakehouse pipeline orchestration routines."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from harness.services.data_management.models import (
    ContractValidationReport,
    EntityRecord,
    MedallionPipelineConfig,
    MedallionPipelineResult,
    QualityScorecard,
    SurvivorshipRule,
)

if TYPE_CHECKING:
    from harness.services.data_management.engine import DataManagementEngine


def execute_medallion_pipeline_stages(
    engine: DataManagementEngine,
    raw_records: list[dict[str, Any]],
    config: MedallionPipelineConfig,
) -> MedallionPipelineResult:
    """Execute full Medallion pipeline (Bronze Ingestion -> Contract & Quality Gate -> Silver MDM -> Gold Mart)."""
    batch_id = f"batch_{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Bronze Tier: Ingest raw payloads with technical metadata
    bronze_records: list[dict[str, Any]] = []
    for idx, r in enumerate(raw_records):
        item = dict(r)
        item["_ingested_at"] = now_iso
        item["_batch_id"] = batch_id
        item["_bronze_id"] = f"{batch_id}_{idx:05d}"
        bronze_records.append(item)

    # 2. Contract Validation Gate
    if config.contract_def:
        contract_report = engine.validate_contract(
            bronze_records,
            config.contract_def,
            max_quarantine_ratio=config.max_quarantine_ratio,
        )
    else:
        contract_report = ContractValidationReport(
            is_compliant=True,
            contract_name="unspecified",
            version="0.0.0",
            total_records=len(bronze_records),
            valid_records=len(bronze_records),
            quarantine_count=0,
            violations=[],
        )

    # Separate clean vs quarantined records
    quarantined_records: list[dict[str, Any]] = []
    valid_records: list[dict[str, Any]] = []

    if not contract_report.is_compliant:
        for idx, r in enumerate(bronze_records):
            q_item = dict(r)
            reasons = [v.message for v in contract_report.violations if v.record_index == idx]
            if not reasons and contract_report.violations:
                reasons = [v.message for v in contract_report.violations]
            q_item["_quarantine_reason"] = reasons or ["Contract non-compliant: batch quarantined"]
            q_item["violations"] = [
                v.to_dict() for v in contract_report.violations if v.record_index == idx
            ] or [v.to_dict() for v in contract_report.violations]
            quarantined_records.append(q_item)
        valid_records = []
    else:
        quarantined_indices = {v.record_index for v in contract_report.violations if v.record_index >= 0}
        for idx, r in enumerate(bronze_records):
            if idx in quarantined_indices:
                q_item = dict(r)
                q_item["_quarantine_reason"] = [
                    v.message for v in contract_report.violations if v.record_index == idx
                ]
                q_item["violations"] = [
                    v.to_dict() for v in contract_report.violations if v.record_index == idx
                ]
                quarantined_records.append(q_item)
            else:
                valid_records.append(r)

    if not valid_records:
        quality_scorecard = QualityScorecard(
            dataset_name=f"silver_{config.contract_def.get('name', 'dataset') if config.contract_def else 'empty'}",
            total_rows=0,
            overall_score=0.0,
            passed=False,
            dimensions={},
            column_profiles={},
        )
        return MedallionPipelineResult(
            batch_id=batch_id,
            bronze_records_count=len(bronze_records),
            silver_records_count=0,
            gold_records_count=0,
            quarantine_records_count=len(quarantined_records),
            contract_report=contract_report,
            quality_scorecard=quality_scorecard,
            golden_records=[],
            quarantined_records=quarantined_records,
            gold_marts=[],
            completed_at=now_iso,
        )

    # 3. Quality Profiling Gate
    req_fields = None
    acc_ranges = None
    if config.quality_rules:
        rules_block = config.quality_rules.get("rules", config.quality_rules)
        req_fields = rules_block.get("completeness", {}).get("required_fields")
        acc_dict = rules_block.get("accuracy", {}).get("numeric_ranges")
        if acc_dict:
            acc_ranges = {k: (float(v[0]), float(v[1])) for k, v in acc_dict.items()}

    quality_scorecard = engine.profile_quality(
        valid_records,
        dataset_name=f"silver_{config.contract_def.get('name', 'dataset') if config.contract_def else 'data'}",
        key_fields=list(config.key_fields),
        required_fields=req_fields,
        accuracy_ranges=acc_ranges,
        pass_threshold=config.pass_quality_threshold,
    )

    # 4. Silver Tier: Master Data Entity Resolution
    entity_records: list[EntityRecord] = []
    for r in valid_records:
        entity_records.append(
            EntityRecord(
                record_id=r.get("trip_id") or r.get("record_id") or r.get("student_id") or r["_bronze_id"],
                source_system=r.get("source_system") or config.source_priority[0],
                updated_at=r.get("event_timestamp") or r.get("updated_at") or now_iso,
                attributes={k: v for k, v in r.items() if not k.startswith("_")},
            )
        )

    surv_rules = {
        k: SurvivorshipRule(v) for k, v in config.survivorship_rules.items()
    }
    golden_records = engine.resolve_golden_records(
        entity_records,
        match_keys=list(config.match_keys if config.match_keys else config.key_fields),
        survivorship_rules=surv_rules,
        source_priority=list(config.source_priority),
    )

    # 5. Gold Tier: Curated Business Marts
    gold_marts: list[dict[str, Any]] = []
    for g in golden_records:
        gold_item = dict(g.resolved_attributes)
        gold_item["master_id"] = g.master_id
        gold_item["_match_confidence"] = g.match_confidence
        gold_item["_source_count"] = g.source_records_count
        gold_marts.append(gold_item)

    return MedallionPipelineResult(
        batch_id=batch_id,
        bronze_records_count=len(bronze_records),
        silver_records_count=len(valid_records),
        gold_records_count=len(gold_marts),
        quarantine_records_count=len(quarantined_records),
        contract_report=contract_report,
        quality_scorecard=quality_scorecard,
        golden_records=golden_records,
        quarantined_records=quarantined_records,
        gold_marts=gold_marts,
        completed_at=now_iso,
    )
