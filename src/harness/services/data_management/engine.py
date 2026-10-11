"""Authoritative domain engine coordinating data lifecycle capabilities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from harness.events.bus import EventBus
from harness.services.data_management.models import (
    ContractValidationReport,
    DataContractValidator,
    DataQualityProfiler,
    EntityRecord,
    GoldenRecord,
    GoldenRecordResolver,
    MaturityAssessor,
    MaturityReport,
    MedallionPipelineConfig,
    MedallionPipelineResult,
    QualityScorecard,
    SurvivorshipRule,
)
from harness.services.data_management.pipeline import execute_medallion_pipeline_stages


class DataManagementEngine:
    """Authoritative domain engine coordinating data lifecycle capabilities."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.event_bus = event_bus

    def validate_contract(
        self,
        records: list[dict[str, Any]],
        contract_def: dict[str, Any],
        max_quarantine_ratio: float = 0.05,
        reference_time: datetime | None = None,
    ) -> ContractValidationReport:
        """Validate dataset records against Open Data Contract definition."""
        validator = DataContractValidator.from_dict(contract_def, reference_time=reference_time)
        return validator.validate_dataset(
            records, max_quarantine_ratio=max_quarantine_ratio, reference_time=reference_time
        )

    def profile_quality(
        self,
        records: list[dict[str, Any]],
        dataset_name: str = "dataset",
        key_fields: list[str] | None = None,
        required_fields: list[str] | None = None,
        accuracy_ranges: dict[str, tuple[float, float]] | None = None,
        validation_rules: dict[str, Any] | None = None,
        consistency_rules: list[dict[str, Any]] | None = None,
        timeliness_field: str | None = None,
        max_latency_hours: float = 24.0,
        pass_threshold: float = 95.0,
        reference_time: datetime | None = None,
    ) -> QualityScorecard:
        """Profile dataset across the 6 DAMA quality dimensions."""
        profiler = DataQualityProfiler(
            key_fields=key_fields,
            required_fields=required_fields,
            accuracy_ranges=accuracy_ranges,
            validation_rules=validation_rules,
            consistency_rules=consistency_rules,
            timeliness_field=timeliness_field,
            max_latency_hours=max_latency_hours,
            pass_threshold=pass_threshold,
            reference_time=reference_time,
        )
        return profiler.profile(records, dataset_name=dataset_name, reference_time=reference_time)

    def resolve_golden_records(
        self,
        records: list[EntityRecord],
        match_keys: list[str] | None = None,
        fuzzy_keys: list[tuple[str, float]] | None = None,
        survivorship_rules: dict[str, SurvivorshipRule] | None = None,
        source_priority: list[str] | None = None,
    ) -> list[GoldenRecord]:
        """Cluster records by entity identity and synthesize canonical Golden Records."""
        resolver = GoldenRecordResolver(
            match_keys=match_keys,
            fuzzy_keys=fuzzy_keys,
            survivorship_rules=survivorship_rules,
            source_priority=source_priority,
        )
        return resolver.resolve(records)

    def assess_maturity(
        self,
        scores: dict[str, int],
        target_level: int = 4,
        organization_name: str = "Enterprise Organization",
    ) -> MaturityReport:
        """Evaluate Level 0–5 Data Management Maturity and generate strategic roadmap."""
        assessor = MaturityAssessor(target_level=target_level)
        return assessor.evaluate_answers(scores, organization_name=organization_name)

    def execute_medallion_pipeline(
        self,
        raw_records: list[dict[str, Any]],
        config: MedallionPipelineConfig,
    ) -> MedallionPipelineResult:
        """Execute full Medallion pipeline (Bronze Ingestion -> Contract & Quality Gate -> Silver MDM -> Gold Mart)."""
        return execute_medallion_pipeline_stages(self, raw_records, config)
