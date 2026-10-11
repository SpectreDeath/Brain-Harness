"""Built-in Data Management Service wrapper for the IoC container."""

from __future__ import annotations

from typing import Any

from harness.events.bus import EventBus
from harness.services.data_management.engine import DataManagementEngine
from harness.services.data_management.models import (
    ContractValidationReport,
    EntityRecord,
    GoldenRecord,
    MaturityReport,
    MedallionPipelineConfig,
    MedallionPipelineResult,
    QualityScorecard,
)


class BuiltinDataManagementService:
    """Built-in implementation of DataManagementService for the IoC container."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self.engine = DataManagementEngine(event_bus=event_bus)

    def get_engine(self) -> DataManagementEngine:
        return self.engine

    def validate_contract(
        self,
        records: list[dict[str, Any]],
        contract_def: dict[str, Any],
        max_quarantine_ratio: float = 0.05,
    ) -> ContractValidationReport:
        return self.engine.validate_contract(records, contract_def, max_quarantine_ratio=max_quarantine_ratio)

    def profile_quality(
        self,
        records: list[dict[str, Any]],
        dataset_name: str = "dataset",
        **kwargs: Any,
    ) -> QualityScorecard:
        return self.engine.profile_quality(records, dataset_name=dataset_name, **kwargs)

    def resolve_golden_records(
        self,
        records: list[EntityRecord],
        **kwargs: Any,
    ) -> list[GoldenRecord]:
        return self.engine.resolve_golden_records(records, **kwargs)

    def assess_maturity(
        self,
        scores: dict[str, int],
        target_level: int = 4,
        organization_name: str = "Enterprise Organization",
    ) -> MaturityReport:
        return self.engine.assess_maturity(scores, target_level=target_level, organization_name=organization_name)

    def execute_medallion_pipeline(
        self,
        raw_records: list[dict[str, Any]],
        config: MedallionPipelineConfig,
    ) -> MedallionPipelineResult:
        return self.engine.execute_medallion_pipeline(raw_records, config)
