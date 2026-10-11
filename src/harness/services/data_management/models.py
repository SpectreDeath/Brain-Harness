"""Slotted data models and configurations for Data Management and Medallion pipelines."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def _ensure_skills_path() -> None:
    """Ensure data-management-architect skill directory is on sys.path."""
    p = Path(__file__).resolve()
    for parent in p.parents:
        candidate = parent / ".agents" / "skills" / "data-management-architect"
        if candidate.exists():
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            break


_ensure_skills_path()

from scripts.data_contract_validator import (  # type: ignore[import-not-found]
    ContractValidationReport,
    DataContractValidator,
)
from scripts.data_quality_profiler import (  # type: ignore[import-not-found]
    DataQualityProfiler,
    QualityScorecard,
)
from scripts.golden_record_resolver import (  # type: ignore[import-not-found]
    EntityRecord,
    GoldenRecord,
    GoldenRecordResolver,
    SurvivorshipRule,
)
from scripts.maturity_assessor import (  # type: ignore[import-not-found]
    MaturityAssessor,
    MaturityReport,
)


@dataclass(slots=True)
class MedallionPipelineConfig:
    """Configuration driving the Medallion lakehouse pipeline execution."""

    contract_def: dict[str, Any] = field(default_factory=dict)
    quality_rules: dict[str, Any] = field(default_factory=dict)
    key_fields: tuple[str, ...] = ("student_id", "national_id")
    source_priority: tuple[str, ...] = ("registrar_system", "mobility_portal", "admissions_crm")
    survivorship_rules: dict[str, str] = field(default_factory=dict)
    max_quarantine_ratio: float = 0.05
    pass_quality_threshold: float = 70.0
    contract_path: str | Path | None = None
    quality_config_path: str | Path | None = None
    source_system: str | None = None
    primary_keys: tuple[str, ...] | list[str] | None = None
    match_keys: tuple[str, ...] | list[str] | None = None
    min_quality_score: float | None = None

    def __post_init__(self) -> None:
        if self.contract_path and not self.contract_def:
            p = Path(self.contract_path)
            if p.exists():
                loaded = yaml.safe_load(p.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    self.contract_def = loaded
        if self.quality_config_path and not self.quality_rules:
            p = Path(self.quality_config_path)
            if p.exists():
                loaded = yaml.safe_load(p.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    self.quality_rules = loaded
        if self.quality_rules and self.min_quality_score is None:
            thresh = self.quality_rules.get("thresholds", {}).get("overall_min_score")
            if thresh is not None:
                self.pass_quality_threshold = float(thresh)
        if self.primary_keys:
            self.key_fields = tuple(self.primary_keys)
        elif self.quality_rules:
            rules_block = self.quality_rules.get("rules", self.quality_rules)
            u_keys = rules_block.get("uniqueness", {}).get("primary_keys")
            if u_keys:
                self.key_fields = tuple(u_keys)
        elif self.match_keys:
            self.key_fields = tuple(self.match_keys)
        if self.source_system and self.source_system not in self.source_priority:
            self.source_priority = (self.source_system,) + self.source_priority
        if self.min_quality_score is not None:
            self.pass_quality_threshold = float(self.min_quality_score)


@dataclass(slots=True)
class MedallionPipelineResult:
    """Consolidated outcome of an end-to-end Medallion pipeline run."""

    batch_id: str
    bronze_records_count: int
    silver_records_count: int
    gold_records_count: int
    quarantine_records_count: int
    contract_report: ContractValidationReport
    quality_scorecard: QualityScorecard
    golden_records: list[GoldenRecord]
    quarantined_records: list[dict[str, Any]]
    gold_marts: list[dict[str, Any]]
    completed_at: str

    @property
    def is_successful(self) -> bool:
        return self.contract_report.is_compliant and self.quality_scorecard.passed

    @property
    def success(self) -> bool:
        return self.is_successful

    @property
    def contract_compliant(self) -> bool:
        return self.contract_report.is_compliant

    @property
    def records_bronze_count(self) -> int:
        return self.bronze_records_count

    @property
    def records_silver_count(self) -> int:
        return self.silver_records_count

    @property
    def records_gold_count(self) -> int:
        return self.gold_records_count

    @property
    def records_quarantine_count(self) -> int:
        return self.quarantine_records_count

    @property
    def gold_records(self) -> list[dict[str, Any]]:
        return self.gold_marts

    @property
    def quarantine_records(self) -> list[dict[str, Any]]:
        return self.quarantined_records

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "is_successful": self.is_successful,
            "success": self.is_successful,
            "bronze_count": self.bronze_records_count,
            "silver_count": self.silver_records_count,
            "gold_count": self.gold_records_count,
            "quarantine_count": self.quarantine_records_count,
            "bronze_records_count": self.bronze_records_count,
            "silver_records_count": self.silver_records_count,
            "gold_records_count": self.gold_records_count,
            "quarantine_records_count": self.quarantine_records_count,
            "contract_report": self.contract_report.to_dict(),
            "quality_scorecard": self.quality_scorecard.to_dict(),
            "golden_records_count": len(self.golden_records),
            "completed_at": self.completed_at,
        }
