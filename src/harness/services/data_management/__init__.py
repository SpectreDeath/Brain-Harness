"""Data Management Service — modular subpackage facade."""

from __future__ import annotations

from harness.services.data_management.engine import DataManagementEngine
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
from harness.services.data_management.plugin import DataManagementPlugin, plugin
from harness.services.data_management.protocols import (
    DATA_MANAGEMENT_SERVICE_KEY,
    DataManagementService,
)
from harness.services.data_management.resolvers import resolve_data_management_service
from harness.services.data_management.service import BuiltinDataManagementService

__all__ = [
    "DATA_MANAGEMENT_SERVICE_KEY",
    "BuiltinDataManagementService",
    "ContractValidationReport",
    "DataContractValidator",
    "DataManagementEngine",
    "DataManagementPlugin",
    "DataManagementService",
    "DataQualityProfiler",
    "EntityRecord",
    "GoldenRecord",
    "GoldenRecordResolver",
    "MaturityAssessor",
    "MaturityReport",
    "MedallionPipelineConfig",
    "MedallionPipelineResult",
    "QualityScorecard",
    "SurvivorshipRule",
    "execute_medallion_pipeline_stages",
    "plugin",
    "resolve_data_management_service",
]
