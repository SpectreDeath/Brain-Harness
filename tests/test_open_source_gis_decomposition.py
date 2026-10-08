"""Characterization test contracts for Open-Source GIS architectural decomposition.

Verifies:
1. Independent submodule imports (models, catalog, validator, visualizer, service)
2. Backward-compatible facade imports from harness.services.open_source_gis
3. Slotted and frozen dataclass immutability (Rule 12 & Rule 43)
4. FalconView defense-restricted domain boundary safety gate
5. CRS planar projection safety invariant on metric operations
6. Single-seam resolver resolve_open_source_gis with fallback and IoC resolution (Rule 58)
7. Root service re-export from harness.services
"""

from __future__ import annotations

import pytest

from harness.kernel.context import ServiceContext


@pytest.mark.unit
class TestOpenSourceGisDecompositionContracts:
    """Contract tests for open_source_gis decomposition and single-seam resolution."""

    def test_submodule_imports(self) -> None:
        """Verify symbols can be imported directly from dedicated domain submodules."""
        from harness.services.open_source_gis.models import (
            CRSProjectionError,
            EngineSelectionResult,
            FalconViewRestrictedDomainError,
            GISEngineRecord,
            GISEngineScore,
            GisVisualBriefResult,
            SpatialArchitectureReceipt,
            SpatialPipelineDAG,
            SpatialPipelineStep,
            SpatialWorkloadProfile,
            TopologyAuditReport,
            TopologyValidationError,
        )
        from harness.services.open_source_gis.catalog import GISEngineCatalog
        from harness.services.open_source_gis.validator import (
            audit_topology,
            validate_pipeline_dag,
        )
        from harness.services.open_source_gis.visualizer import generate_visual_brief
        from harness.services.open_source_gis.service import (
            OPEN_SOURCE_GIS_SERVICE_KEY,
            DefaultOpenSourceGisService,
            OpenSourceGisService,
            resolve_open_source_gis,
        )

        assert issubclass(FalconViewRestrictedDomainError, ValueError)
        assert issubclass(CRSProjectionError, ValueError)
        assert issubclass(TopologyValidationError, ValueError)
        assert callable(audit_topology)
        assert callable(validate_pipeline_dag)
        assert callable(generate_visual_brief)
        assert callable(resolve_open_source_gis)
        assert OPEN_SOURCE_GIS_SERVICE_KEY is not None

    def test_backward_compatible_facade_imports(self) -> None:
        """Verify 100% backward compatibility of all existing imports from facade root."""
        from harness.services.open_source_gis import (
            CRSProjectionError,
            DefaultOpenSourceGisService,
            EngineSelectionResult,
            FalconViewRestrictedDomainError,
            GISEngineCatalog,
            GISEngineRecord,
            GISEngineScore,
            GisVisualBriefResult,
            OPEN_SOURCE_GIS_SERVICE_KEY,
            OpenSourceGisService,
            SpatialArchitectureReceipt,
            SpatialPipelineDAG,
            SpatialPipelineStep,
            SpatialWorkloadProfile,
            TopologyAuditReport,
            TopologyValidationError,
            resolve_open_source_gis,
        )

        assert OpenSourceGisService is not None
        assert DefaultOpenSourceGisService is not None
        assert GISEngineCatalog is not None
        assert callable(resolve_open_source_gis)

    def test_slotted_frozen_dataclass_immutability(self) -> None:
        """Verify slotted and frozen immutability across all domain models (Rule 12, Rule 43)."""
        from harness.services.open_source_gis.models import (
            GISEngineRecord,
            GISEngineScore,
            SpatialPipelineStep,
            SpatialWorkloadProfile,
            TopologyAuditReport,
        )

        profile = SpatialWorkloadProfile(
            geometry_type="vector_polygon",
            domain="cartography",
            sector="civilian",
        )
        with pytest.raises((AttributeError, TypeError)):
            profile.domain = "mutated"  # type: ignore

        rec = GISEngineRecord(
            name="TestEngine",
            star_rating=4.5,
            license="MIT",
            maturity="production",
            sector_flags=("civilian",),
            primary_domains=("general_gis",),
            specialized_tools=("ToolA",),
            python_api="test_api",
            supported_formats=("GeoPackage",),
            negative_boundary="None",
            arcgis_parity=False,
            article_note="Note",
        )
        with pytest.raises((AttributeError, TypeError)):
            rec.name = "MutatedName"  # type: ignore

        step = SpatialPipelineStep(
            step_id=1,
            operation="reproject",
            engine="qgis",
            input_crs="EPSG:4326",
            output_crs="EPSG:32632",
            input_format="GeoPackage",
            output_format="GeoPackage",
        )
        with pytest.raises((AttributeError, TypeError)):
            step.operation = "mutated_op"  # type: ignore

        topo = TopologyAuditReport(
            is_valid=True,
            sliver_count=0,
            self_intersection_count=0,
            unclosed_rings=0,
            duplicate_vertices=0,
            repair_actions=(),
            severity="OK",
        )
        with pytest.raises((AttributeError, TypeError)):
            topo.is_valid = False  # type: ignore

    def test_falconview_defense_boundary(self) -> None:
        """Verify that defense-restricted workloads halt under safety boundary."""
        from harness.services.open_source_gis.models import (
            FalconViewRestrictedDomainError,
            SpatialWorkloadProfile,
        )

        with pytest.raises(FalconViewRestrictedDomainError, match="defense_restricted"):
            SpatialWorkloadProfile(
                geometry_type="vector_polygon",
                domain="tactical_flight",
                sector="defense_restricted",
            )

    def test_crs_projection_safety_invariant(self) -> None:
        """Verify metric spatial calculations cannot execute on unprojected geographic CRS."""
        from harness.services.open_source_gis.models import (
            CRSProjectionError,
            SpatialPipelineStep,
        )

        with pytest.raises(CRSProjectionError, match="unprojected geographic CRS"):
            SpatialPipelineStep(
                step_id=1,
                operation="buffer",
                engine="qgis",
                input_crs="EPSG:4326",
                output_crs="EPSG:4326",
                input_format="GeoPackage",
                output_format="GeoPackage",
            )

    def test_resolve_open_source_gis_fallback_and_ioc(self) -> None:
        """Verify single-seam resolver fallback and IoC resolution (Rule 58)."""
        from harness.services.open_source_gis.service import (
            OPEN_SOURCE_GIS_SERVICE_KEY,
            DefaultOpenSourceGisService,
            OpenSourceGisService,
            resolve_open_source_gis,
        )

        # Fallback on None
        svc_none = resolve_open_source_gis(None)
        assert isinstance(svc_none, DefaultOpenSourceGisService)
        assert isinstance(svc_none, OpenSourceGisService)

        # Fallback on empty context
        ctx_empty = ServiceContext()
        svc_empty = resolve_open_source_gis(ctx_empty)
        assert isinstance(svc_empty, DefaultOpenSourceGisService)

        # Resolution from registered context
        ctx_populated = ServiceContext()
        custom_svc = DefaultOpenSourceGisService()
        ctx_populated.provide(OPEN_SOURCE_GIS_SERVICE_KEY, custom_svc)
        resolved = resolve_open_source_gis(ctx_populated)
        assert resolved is custom_svc

    def test_root_services_reexport(self) -> None:
        """Verify resolver and core classes are re-exported from harness.services root."""
        from harness.services import (
            DefaultOpenSourceGisService,
            GISEngineCatalog,
            OpenSourceGisService,
            resolve_open_source_gis,
        )

        assert callable(resolve_open_source_gis)
        svc = resolve_open_source_gis()
        assert isinstance(svc, DefaultOpenSourceGisService)
        assert isinstance(svc, OpenSourceGisService)
        assert GISEngineCatalog is not None
