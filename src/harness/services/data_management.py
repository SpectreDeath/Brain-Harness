"""Data Management Service and Unified Engine.

Deepened architecture seam providing an authoritative facade across:
1. Open Data Contract validation (ODCS)
2. 6-Dimension DAMA data quality profiling
3. Master Data Management entity resolution and Golden Record survivorship
4. Level 0–5 Data Management Maturity assessment
5. End-to-end Medallion Lakehouse pipeline orchestration (Bronze -> Silver -> Gold)
"""

from __future__ import annotations

# Reuse core script implementations
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import structlog
import yaml

from harness.events.bus import EVENT_BUS_KEY, EventBus
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.plugins.manifest import PluginManifest

_skills_dir = Path(__file__).resolve().parent.parent.parent.parent / ".agents" / "skills" / "data-management-architect"
if str(_skills_dir) not in sys.path:
    sys.path.insert(0, str(_skills_dir))

from scripts.data_contract_validator import (
    ContractValidationReport,
    DataContractValidator,
)
from scripts.data_quality_profiler import (
    DataQualityProfiler,
    QualityScorecard,
)
from scripts.golden_record_resolver import (
    EntityRecord,
    GoldenRecord,
    GoldenRecordResolver,
    SurvivorshipRule,
)
from scripts.maturity_assessor import (
    MaturityAssessor,
    MaturityReport,
)

logger = structlog.get_logger()


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
        report = validator.validate_dataset(
            records, max_quarantine_ratio=max_quarantine_ratio, reference_time=reference_time
        )
        return report

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
        scorecard = profiler.profile(records, dataset_name=dataset_name, reference_time=reference_time)
        return scorecard

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
            contract_report = self.validate_contract(
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

        quality_scorecard = self.profile_quality(
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
        golden_records = self.resolve_golden_records(
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


DATA_MANAGEMENT_SERVICE_KEY = ServiceKey[DataManagementService]("harness.services.data_management")


class DataManagementPlugin(HarnessPlugin):
    """Built-in plugin providing the Data Management service and registering agent tools."""

    name = "data_management"
    version = "1.0.0"
    description = "Enterprise Data Management, ODCS contracts, quality profiling, and Medallion pipelines"

    def __init__(self) -> None:
        self._service: BuiltinDataManagementService | None = None

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [DATA_MANAGEMENT_SERVICE_KEY]

    @property
    def trusted(self) -> bool:
        return True

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name=self.name,
            version=self.version,
            description=self.description,
            provides=["data_management"],
        )

    async def on_load(self, ctx: ServiceContext) -> None:
        bus = ctx.optional(EVENT_BUS_KEY)
        self._service = BuiltinDataManagementService(event_bus=bus)
        ctx.provide(DATA_MANAGEMENT_SERVICE_KEY, self._service, provider=self.name)
        logger.info("Data management service registered", provider=self.name)

    async def on_unload(self) -> None:
        self._service = None

    async def on_enable(self) -> None:
        pass

    async def on_disable(self) -> None:
        pass

    async def enable(self, ctx: ServiceContext) -> None:
        await self.on_load(ctx)
        await self.on_enable()

    async def disable(self, ctx: ServiceContext | None = None) -> None:
        await self.on_disable()
        await self.on_unload()
