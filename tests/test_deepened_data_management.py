"""Tests for deepened enterprise data management subsystem.

Verifies:
1. DataManagementEngine end-to-end Medallion pipeline execution (Bronze -> Silver -> Gold).
2. IoC container registration and retrieval via DATA_MANAGEMENT_SERVICE_KEY.
3. BuiltinDataManagementService and DataManagementPlugin lifecycle.
4. Direct async command functions in harness.commands.data.
5. Headless Click CLI commands (harness data validate/profile/resolve/maturity/pipeline).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from click.testing import CliRunner

from harness.cli import main
from harness.commands.data import (
    assess_maturity_cmd,
    profile_quality_cmd,
    resolve_golden_records_cmd,
    run_medallion_pipeline_cmd,
    validate_contract_cmd,
)
from harness.kernel.context import ServiceContext
from harness.services.data_management import (
    DATA_MANAGEMENT_SERVICE_KEY,
    BuiltinDataManagementService,
    DataManagementEngine,
    DataManagementPlugin,
    MedallionPipelineConfig,
    MedallionPipelineResult,
)


@pytest.fixture
def sample_records() -> list[dict[str, Any]]:
    return [
        {
            "record_id": "REC-001",
            "student_id": "STU-001",
            "full_name": "Alice Martin",
            "email": "alice@example.edu",
            "campus_distance_km": 12.5,
            "rideshare_benefit_approved": True,
            "source_system": "registrar_system",
            "updated_at": "2026-03-01T10:00:00Z",
        },
        {
            "record_id": "REC-002",
            "student_id": "STU-001",
            "full_name": "Alice M.",
            "email": "alice@example.edu",
            "campus_distance_km": 14.0,
            "rideshare_benefit_approved": True,
            "source_system": "mobility_portal",
            "updated_at": "2026-03-05T12:00:00Z",
        },
        {
            "record_id": "REC-003",
            "student_id": "STU-002",
            "full_name": "Bob Chen",
            "email": "bob@example.edu",
            "campus_distance_km": 5.2,
            "rideshare_benefit_approved": False,
            "source_system": "registrar_system",
            "updated_at": "2026-03-02T09:00:00Z",
        },
    ]


@pytest.fixture
def contract_file(tmp_path: Path) -> Path:
    contract_data = {
        "dataset_name": "dim_student",
        "version": "1.0.0",
        "description": "Student master records",
        "owner": "Registrar Office",
        "schema": {
            "fields": [
                {"name": "record_id", "type": "string", "required": False, "nullable": True},
                {"name": "student_id", "type": "string", "required": True, "nullable": False},
                {"name": "full_name", "type": "string", "required": True, "nullable": False},
                {"name": "email", "type": "string", "required": True, "nullable": False},
                {"name": "campus_distance_km", "type": "float", "required": False, "nullable": True},
                {"name": "rideshare_benefit_approved", "type": "boolean", "required": False, "nullable": True},
            ]
        },
        "sla": {"freshness": "24h", "latency": "1h"},
    }
    contract_path = tmp_path / "student_contract.yaml"
    with open(contract_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(contract_data, f)
    return contract_path


@pytest.fixture
def quality_config_file(tmp_path: Path) -> Path:
    quality_data = {
        "thresholds": {"overall_min_score": 70.0},
        "rules": {
            "accuracy": {"numeric_ranges": {"campus_distance_km": [0.0, 200.0]}},
            "completeness": {"required_fields": ["student_id", "email"]},
            "consistency": [],
            "timeliness": {"max_age_days": 365},
            "validity": {"regex_patterns": {"email": r"^[^@]+@[^@]+\.[^@]+$"}},
            "uniqueness": {"primary_keys": ["record_id"]},
        },
    }
    config_path = tmp_path / "quality_config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(quality_data, f)
    return config_path


@pytest.fixture
def maturity_survey_file(tmp_path: Path) -> Path:
    survey_data = {
        "organization": "University Mobility Network",
        "capabilities": {
            "data_governance": {"level": 3, "score": 3.2, "notes": "Formal CDO office and data council"},
            "data_architecture": {"level": 3, "score": 3.0, "notes": "Medallion lakehouse architecture"},
            "data_modeling": {"level": 2, "score": 2.5, "notes": "Normalized operational models"},
            "data_quality": {"level": 3, "score": 3.1, "notes": "Automated 6-dimension profiling in CI"},
            "data_security": {"level": 4, "score": 4.0, "notes": "Role-based masking and RBAC"},
            "data_operations": {"level": 3, "score": 3.0, "notes": "Airflow DAGs and dbt pipelines"},
        },
    }
    survey_path = tmp_path / "maturity_survey.yaml"
    with open(survey_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(survey_data, f)
    return survey_path


# ============================================================================
# 1. Test DataManagementEngine (Medallion Pipeline)
# ============================================================================

@pytest.mark.unit
class TestDataManagementEngine:
    """Test suite for DataManagementEngine medallion operations."""

    def test_execute_medallion_pipeline_success(
        self,
        sample_records: list[dict[str, Any]],
        contract_file: Path,
        quality_config_file: Path,
    ) -> None:
        engine = DataManagementEngine()
        config = MedallionPipelineConfig(
            contract_path=contract_file,
            quality_config_path=quality_config_file,
            source_system="registrar_system",
            min_quality_score=60.0,
            primary_keys=("record_id",),
            match_keys=("student_id",),
            source_priority=("registrar_system", "mobility_portal"),
        )
        result = engine.execute_medallion_pipeline(sample_records, config)

        assert isinstance(result, MedallionPipelineResult)
        assert result.success is True
        assert result.records_bronze_count == 3
        assert result.records_silver_count == 3
        # Deduplicated into 2 unique student entities: STU-001 and STU-002
        assert result.records_gold_count == 2
        assert result.records_quarantine_count == 0
        assert result.contract_compliant is True
        assert result.quality_scorecard is not None
        assert result.quality_scorecard.passed is True
        assert len(result.gold_records) == 2

        # Check survivorship in gold record STU-001:
        # registrar_system takes priority for full_name: "Alice Martin"
        stu_1 = next(r for r in result.gold_records if r["student_id"] == "STU-001")
        assert stu_1["full_name"] == "Alice Martin"

    def test_execute_medallion_pipeline_quarantined_on_invalid_contract(
        self,
        contract_file: Path,
    ) -> None:
        invalid_records = [
            {"student_id": "STU-999", "campus_distance_km": 10.0}  # Missing full_name & email
        ]
        engine = DataManagementEngine()
        config = MedallionPipelineConfig(
            contract_path=contract_file,
            source_system="admissions_crm",
        )
        result = engine.execute_medallion_pipeline(invalid_records, config)

        assert result.success is False
        assert result.contract_compliant is False
        assert result.records_bronze_count == 1
        assert result.records_silver_count == 0
        assert result.records_gold_count == 0
        assert result.records_quarantine_count == 1
        assert len(result.quarantine_records) == 1
        assert "violations" in result.quarantine_records[0]

    def test_execute_medallion_pipeline_without_contract_and_quality(
        self,
        sample_records: list[dict[str, Any]],
    ) -> None:
        engine = DataManagementEngine()
        config = MedallionPipelineConfig(
            source_system="default_feed",
            primary_keys=("record_id",),
            match_keys=("student_id",),
        )
        result = engine.execute_medallion_pipeline(sample_records, config)

        assert result.success is True
        assert result.records_bronze_count == 3
        assert result.records_gold_count == 2
        assert result.contract_compliant is True


# ============================================================================
# 2. Test Service Key, IoC Registration & Plugin Lifecycle
# ============================================================================

@pytest.mark.unit
class TestServiceRegistrationAndPlugin:
    """Test suite for IoC container and DataManagementPlugin."""

    def test_ioc_context_provision_and_retrieval(self) -> None:
        context = ServiceContext()
        engine = DataManagementEngine()
        context.provide(DATA_MANAGEMENT_SERVICE_KEY, engine)

        resolved = context.require(DATA_MANAGEMENT_SERVICE_KEY)
        assert resolved is engine

    def test_builtin_data_management_service_instantiation(self) -> None:
        service = BuiltinDataManagementService()
        assert isinstance(service.engine, DataManagementEngine)
        assert service.engine is service.engine

    @pytest.mark.asyncio
    async def test_plugin_manifest_and_lifecycle(self) -> None:
        plugin = DataManagementPlugin()
        assert plugin.name == "data_management"
        assert plugin.manifest.name == "data_management"
        assert "data_management" in plugin.manifest.provides

        context = ServiceContext()
        await plugin.enable(context)
        resolved = context.require(DATA_MANAGEMENT_SERVICE_KEY)
        assert isinstance(resolved, (BuiltinDataManagementService, DataManagementEngine))
        assert isinstance(resolved.engine, DataManagementEngine)

        await plugin.disable(context)


# ============================================================================
# 3. Test Async Command Runners
# ============================================================================

@pytest.mark.unit
class TestAsyncCommands:
    """Test pure async commands in harness.commands.data."""

    @pytest.mark.asyncio
    async def test_validate_contract_cmd(
        self,
        sample_records: list[dict[str, Any]],
        contract_file: Path,
        tmp_path: Path,
    ) -> None:
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_records), encoding="utf-8")

        result = await validate_contract_cmd(
            dataset_path=str(data_file),
            contract_path=str(contract_file),
        )
        assert result["valid"] is True
        assert result["total_records"] == 3
        assert result["violations_count"] == 0

    @pytest.mark.asyncio
    async def test_profile_quality_cmd(
        self,
        sample_records: list[dict[str, Any]],
        quality_config_file: Path,
        tmp_path: Path,
    ) -> None:
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_records), encoding="utf-8")

        result = await profile_quality_cmd(
            dataset_path=str(data_file),
            rules_path=str(quality_config_file),
        )
        assert result["passed"] is True
        assert result["overall_score"] >= 70.0
        assert "dimensions" in result

    @pytest.mark.asyncio
    async def test_resolve_golden_records_cmd(
        self,
        sample_records: list[dict[str, Any]],
        tmp_path: Path,
    ) -> None:
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_records), encoding="utf-8")

        result = await resolve_golden_records_cmd(
            dataset_path=str(data_file),
            match_keys="student_id",
            source_priority="registrar_system,mobility_portal",
        )
        assert result["input_records"] == 3
        assert result["golden_records_count"] == 2

    @pytest.mark.asyncio
    async def test_assess_maturity_cmd(
        self,
        maturity_survey_file: Path,
    ) -> None:
        result = await assess_maturity_cmd(
            survey_path=str(maturity_survey_file),
        )
        assert result["organization"] == "University Mobility Network"
        assert result["overall_level"] >= 2
        assert "capabilities" in result

    @pytest.mark.asyncio
    async def test_run_medallion_pipeline_cmd(
        self,
        sample_records: list[dict[str, Any]],
        contract_file: Path,
        quality_config_file: Path,
        tmp_path: Path,
    ) -> None:
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_records), encoding="utf-8")

        result = await run_medallion_pipeline_cmd(
            dataset_path=str(data_file),
            contract_path=str(contract_file),
            quality_path=str(quality_config_file),
            source_system="registrar_system",
            primary_keys="record_id",
        )
        assert result["success"] is True
        assert result["bronze_count"] == 3
        assert result["gold_count"] == 2
        assert result["quarantine_count"] == 0


# ============================================================================
# 4. Test Headless Click CLI Subcommands
# ============================================================================

@pytest.mark.unit
class TestCliCommands:
    """Test Click CLI command group: harness data ..."""

    def test_harness_data_help(self) -> None:
        runner = CliRunner()
        res = runner.invoke(main, ["data", "--help"])
        assert res.exit_code == 0
        assert "Enterprise data management, contracts, quality" in res.output
        assert "validate" in res.output
        assert "profile" in res.output
        assert "resolve" in res.output
        assert "maturity" in res.output
        assert "pipeline" in res.output

    def test_cli_validate_contract(
        self,
        sample_records: list[dict[str, Any]],
        contract_file: Path,
        tmp_path: Path,
    ) -> None:
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_records), encoding="utf-8")

        runner = CliRunner()
        # Normal text output
        res = runner.invoke(
            main,
            ["data", "validate", "--dataset", str(data_file), "--contract", str(contract_file)],
        )
        assert res.exit_code == 0
        assert "Open Data Contract Validation" in res.output
        assert "Compliant" in res.output

        # JSON output
        res_json = runner.invoke(
            main,
            ["data", "validate", "--dataset", str(data_file), "--contract", str(contract_file), "--json"],
        )
        assert res_json.exit_code == 0
        parsed = json.loads(res_json.output)
        assert parsed["valid"] is True

    def test_cli_profile_quality(
        self,
        sample_records: list[dict[str, Any]],
        quality_config_file: Path,
        tmp_path: Path,
    ) -> None:
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_records), encoding="utf-8")

        runner = CliRunner()
        res = runner.invoke(
            main,
            ["data", "profile", "--dataset", str(data_file), "--rules", str(quality_config_file)],
        )
        assert res.exit_code == 0
        assert "Data Quality Profile Report" in res.output

        # Markdown output
        res_md = runner.invoke(
            main,
            ["data", "profile", "--dataset", str(data_file), "--rules", str(quality_config_file), "--markdown"],
        )
        assert res_md.exit_code == 0
        assert "# Data Quality Scorecard" in res_md.output

    def test_cli_resolve_golden_records(
        self,
        sample_records: list[dict[str, Any]],
        tmp_path: Path,
    ) -> None:
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_records), encoding="utf-8")

        runner = CliRunner()
        res = runner.invoke(
            main,
            ["data", "resolve", "--dataset", str(data_file), "--keys", "student_id"],
        )
        assert res.exit_code == 0
        assert "Golden Records Resolution" in res.output
        assert "Golden entities generated: 2" in res.output

    def test_cli_assess_maturity(
        self,
        maturity_survey_file: Path,
    ) -> None:
        runner = CliRunner()
        res = runner.invoke(
            main,
            ["data", "maturity", "--survey", str(maturity_survey_file)],
        )
        assert res.exit_code == 0
        assert "Data Management Maturity Assessment" in res.output
        assert "Level 3" in res.output or "Level" in res.output

        # Summary output
        res_summary = runner.invoke(
            main,
            ["data", "maturity", "--survey", str(maturity_survey_file), "--summary"],
        )
        assert res_summary.exit_code == 0
        assert "University Mobility Network" in res_summary.output

    def test_cli_medallion_pipeline(
        self,
        sample_records: list[dict[str, Any]],
        contract_file: Path,
        quality_config_file: Path,
        tmp_path: Path,
    ) -> None:
        data_file = tmp_path / "data.json"
        data_file.write_text(json.dumps(sample_records), encoding="utf-8")

        runner = CliRunner()
        res = runner.invoke(
            main,
            [
                "data",
                "pipeline",
                "--dataset",
                str(data_file),
                "--contract",
                str(contract_file),
                "--quality",
                str(quality_config_file),
                "--source",
                "registrar_system",
                "--keys",
                "record_id",
            ],
        )
        assert res.exit_code == 0
        assert "Medallion Pipeline Execution" in res.output
        assert "SUCCESS" in res.output
        assert "Gold records: 2" in res.output

        # JSON output
        res_json = runner.invoke(
            main,
            [
                "data",
                "pipeline",
                "--dataset",
                str(data_file),
                "--contract",
                str(contract_file),
                "--quality",
                str(quality_config_file),
                "--source",
                "registrar_system",
                "--keys",
                "record_id",
                "--json",
            ],
        )
        assert res_json.exit_code == 0
        parsed = json.loads(res_json.output)
        assert parsed["success"] is True
        assert parsed["gold_count"] == 2
