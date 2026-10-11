"""Protocols and ServiceKey definitions for the Data Management service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey
from harness.services.data_management.models import (
    ContractValidationReport,
    EntityRecord,
    GoldenRecord,
    MaturityReport,
    MedallionPipelineConfig,
    MedallionPipelineResult,
    QualityScorecard,
)

if TYPE_CHECKING:
    from harness.services.data_management.engine import DataManagementEngine


@runtime_checkable
class DataManagementService(Protocol):
    """Protocol defining the Data Management Service interface."""

    def get_engine(self) -> DataManagementEngine:
        ...

    def validate_contract(
        self,
        records: list[dict[str, Any]],
        contract_def: dict[str, Any],
        max_quarantine_ratio: float = 0.05,
    ) -> ContractValidationReport:
        ...

    def profile_quality(
        self,
        records: list[dict[str, Any]],
        dataset_name: str = "dataset",
        **kwargs: Any,
    ) -> QualityScorecard:
        ...

    def resolve_golden_records(
        self,
        records: list[EntityRecord],
        **kwargs: Any,
    ) -> list[GoldenRecord]:
        ...

    def assess_maturity(
        self,
        scores: dict[str, int],
        target_level: int = 4,
        organization_name: str = "Enterprise Organization",
    ) -> MaturityReport:
        ...

    def execute_medallion_pipeline(
        self,
        raw_records: list[dict[str, Any]],
        config: MedallionPipelineConfig,
    ) -> MedallionPipelineResult:
        ...


DATA_MANAGEMENT_SERVICE_KEY = ServiceKey[DataManagementService]("harness.services.data_management")
