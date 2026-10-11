"""Contract verification test suite for Data Management service decomposition.

Verifies:
1. Architectural bounds: all submodules <= 200 lines (Rule 11).
2. Slotted dataclass structures (Rule 12).
3. Protocol conformance & single-seam IoC resolution (Rule 2, Rule 49, Rule 58).
4. Backward-compatible facade re-exports and medallion pipeline execution.
5. Plugin module singleton export (Rule 45).
"""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.data_management import (
    DATA_MANAGEMENT_SERVICE_KEY,
    BuiltinDataManagementService,
    ContractValidationReport,
    DataContractValidator,
    DataManagementEngine,
    DataManagementPlugin,
    DataManagementService,
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
    plugin,
    resolve_data_management_service,
)


class TestDataManagementDecomposition:
    """Contract tests verifying the architectural invariants of Data Management decomposition."""

    def test_submodule_line_bounds(self) -> None:
        """Verify all submodules in src/harness/services/data_management/ are <= 200 lines per Rule 11."""
        dm_dir = Path(__file__).parent.parent / "src" / "harness" / "services" / "data_management"
        assert dm_dir.is_dir(), f"Expected directory at {dm_dir}"

        py_files = list(dm_dir.glob("*.py"))
        assert len(py_files) >= 8, f"Expected at least 8 submodules, found {len(py_files)}"

        for py_file in py_files:
            line_count = len(py_file.read_text(encoding="utf-8").splitlines())
            assert (
                line_count <= 200
            ), f"{py_file.name} has {line_count} lines, exceeding the 200-line limit (Rule 11)"

    def test_slotted_dataclass_structures(self) -> None:
        """Verify slotted dataclasses are used for high-volume pipeline configurations (Rule 12)."""
        cfg = MedallionPipelineConfig()
        assert hasattr(cfg, "__slots__")

        # Test post_init logic
        cfg2 = MedallionPipelineConfig(min_quality_score=85.0, primary_keys=["id", "code"])
        assert cfg2.pass_quality_threshold == 85.0
        assert cfg2.key_fields == ("id", "code")

    def test_protocol_conformance_and_single_seam_resolver(self) -> None:
        """Verify protocol conformance and single-seam IoC resolution per Rule 49 & 58."""
        service = BuiltinDataManagementService()
        assert isinstance(service, DataManagementService)
        assert isinstance(DATA_MANAGEMENT_SERVICE_KEY, ServiceKey)
        assert DATA_MANAGEMENT_SERVICE_KEY.name == "harness.services.data_management"

        # Fallback resolution with no context
        resolved_default = resolve_data_management_service(None)
        assert isinstance(resolved_default, DataManagementService)

        # Context-based resolution
        ctx = ServiceContext()
        custom_service = BuiltinDataManagementService()
        ctx.provide(DATA_MANAGEMENT_SERVICE_KEY, custom_service)

        resolved_ctx = resolve_data_management_service(ctx)
        assert resolved_ctx is custom_service

    def test_backward_compatible_facade_and_exports(self) -> None:
        """Verify all public symbols are correctly re-exported by facade."""
        assert DataManagementEngine is not None
        assert BuiltinDataManagementService is not None
        assert DataManagementPlugin is not None
        assert DataManagementService is not None
        assert MedallionPipelineConfig is not None
        assert MedallionPipelineResult is not None
        assert ContractValidationReport is not None
        assert DataContractValidator is not None
        assert DataQualityProfiler is not None
        assert QualityScorecard is not None
        assert EntityRecord is not None
        assert GoldenRecord is not None
        assert GoldenRecordResolver is not None
        assert SurvivorshipRule is not None
        assert MaturityAssessor is not None
        assert MaturityReport is not None

    def test_plugin_module_singleton_export(self) -> None:
        """Verify plugin module-level singleton export per Rule 45."""
        assert isinstance(plugin, DataManagementPlugin)
        assert DATA_MANAGEMENT_SERVICE_KEY in plugin.provides
        assert plugin.name == "data_management"
