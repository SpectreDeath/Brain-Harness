"""Data Management CLI command package and pure async execution entrypoints.

Provides headless execution seams for:
- Open Data Contract validation
- 6-Dimension data quality profiling
- Master Data Golden Record entity resolution
- Level 0–5 Data Management Maturity assessment
- End-to-end Medallion lakehouse pipeline runs
- DeepSelect TopK mathematical bounds and kernel configuration
"""

from __future__ import annotations

from harness.commands.data.cli import (
    data_group,
    maturity_cli,
    pipeline_cli,
    profile_cli,
    resolve_cli,
    validate_cli,
)
from harness.commands.data.contracts import validate_contract_cmd
from harness.commands.data.golden_records import resolve_golden_records_cmd
from harness.commands.data.maturity import assess_maturity_cmd
from harness.commands.data.pipeline import run_medallion_pipeline_cmd
from harness.commands.data.quality import profile_quality_cmd
from harness.commands.data.topk import (
    topk_analyze_cmd,
    topk_bounds_cmd,
    topk_recommend_cmd,
)
from harness.commands.data.topk_cli import (
    topk_analyze_cli,
    topk_bounds_cli,
    topk_recommend_cli,
)
from harness.services.data_management import (
    ContractValidationReport,
    DataManagementEngine,
    EntityRecord,
    GoldenRecord,
    MaturityReport,
    MedallionPipelineConfig,
    MedallionPipelineResult,
    QualityScorecard,
)

__all__ = [
    "ContractValidationReport",
    "DataManagementEngine",
    "EntityRecord",
    "GoldenRecord",
    "MaturityReport",
    "MedallionPipelineConfig",
    "MedallionPipelineResult",
    "QualityScorecard",
    "assess_maturity_cmd",
    "data_group",
    "maturity_cli",
    "pipeline_cli",
    "profile_cli",
    "profile_quality_cmd",
    "resolve_cli",
    "resolve_golden_records_cmd",
    "run_medallion_pipeline_cmd",
    "topk_analyze_cli",
    "topk_analyze_cmd",
    "topk_bounds_cli",
    "topk_bounds_cmd",
    "topk_recommend_cli",
    "topk_recommend_cmd",
    "validate_cli",
    "validate_contract_cmd",
]
