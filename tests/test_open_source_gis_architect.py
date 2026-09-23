"""Test contracts and behavioral verification for open-source-gis-architect skill."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import pytest
import yaml

from harness.creator.skills import SkillValidator
from plugins.memory_and_epistemics.skill_knowledge_graph.parser import SkillCardParser

# Import domain engine components
SKILL_ROOT = Path(__file__).parent.parent / ".agents" / "skills" / "open-source-gis-architect"
import sys

if str(SKILL_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from engine import (  # noqa: E402
    CRSProjectionError,
    EngineSelectionResult,
    FalconViewRestrictedDomainError,
    GISEngineCatalog,
    GISEngineRecord,
    GISEngineScore,
    SpatialPipelineDAG,
    SpatialPipelineStep,
    SpatialWorkloadProfile,
    TopologyAuditReport,
)
from spatial_pipeline_validator import validate_steps  # noqa: E402
from topology_hygiene_checker import audit_polygon_rings  # noqa: E402


@pytest.mark.unit
class TestSlottedFrozenDomainModels:
    """Verify Rule 12 and Rule 43: slotted and frozen immutability assertions."""

    def test_slotted_frozen_immutability(self) -> None:
        profile = SpatialWorkloadProfile(
            geometry_type="vector_polygon",
            domain="general_gis",
            data_formats=("GeoPackage",),
        )
        # Rule 43: Direct attribute assignment inside pytest.raises((AttributeError, TypeError))
        with pytest.raises((AttributeError, TypeError)):
            profile.domain = "other"  # type: ignore

        rec = GISEngineRecord(
            name="TestGIS",
            star_rating=4.0,
            license="GPL-2.0",
            maturity="production",
            sector_flags=("civilian",),
            primary_domains=("general_gis",),
            specialized_tools=("ToolA",),
            python_api="test_api",
            supported_formats=("GeoPackage",),
            negative_boundary="None",
            arcgis_parity=True,
            article_note="Note",
        )
        with pytest.raises((AttributeError, TypeError)):
            rec.star_rating = 5.0  # type: ignore

        score = GISEngineScore(
            engine=rec,
            fitness_score=0.9,
            matched_domains=("general_gis",),
            matched_formats=("GeoPackage",),
        )
        with pytest.raises((AttributeError, TypeError)):
            score.fitness_score = 0.5  # type: ignore

        result = EngineSelectionResult(
            primary=score,
            secondary=None,
            composite_score=0.9,
            routing_path="general_path",
            rationale="Test rationale",
        )
        with pytest.raises((AttributeError, TypeError)):
            result.composite_score = 0.1  # type: ignore

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
            step.step_id = 2  # type: ignore

        report = TopologyAuditReport(
            is_valid=True,
            sliver_count=0,
            self_intersection_count=0,
            unclosed_rings=0,
            duplicate_vertices=0,
        )
        with pytest.raises((AttributeError, TypeError)):
            report.is_valid = False  # type: ignore


@pytest.mark.unit
class TestDeterministicEngineRouting:
    """Verify deterministic routing across 14 engines grounded in GIS Geography literature."""

    @pytest.fixture
    def catalog(self) -> GISEngineCatalog:
        return GISEngineCatalog()

    def test_lidar_routes_to_whitebox(self, catalog: GISEngineCatalog) -> None:
        workload = SpatialWorkloadProfile(
            geometry_type="point_cloud",
            domain="lidar_hydrology",
            data_formats=("LAS", "LAZ"),
            has_lidar=True,
        )
        result = catalog.route_workload(workload)
        assert result.primary.engine.name == "Whitebox GAT"
        assert result.routing_path == "lidar_hydrology_whitebox_gat"
        assert result.composite_score >= 0.90

    def test_dem_routes_to_saga(self, catalog: GISEngineCatalog) -> None:
        workload = SpatialWorkloadProfile(
            geometry_type="raster_dem",
            domain="terrain_morphometry",
            analysis="twi",
            data_formats=("GeoTIFF",),
        )
        result = catalog.route_workload(workload)
        assert result.primary.engine.name == "SAGA GIS"
        assert result.routing_path == "terrain_morphometry_saga_gis"
        assert "Topographic Wetness Index" in result.rationale

    def test_spatial_regression_routes_to_geoda(self, catalog: GISEngineCatalog) -> None:
        workload = SpatialWorkloadProfile(
            geometry_type="vector_polygon",
            domain="spatial_statistics",
            needs_statistics=True,
            analysis="moran_i",
            data_formats=("Shapefile",),
        )
        result = catalog.route_workload(workload)
        assert result.primary.engine.name == "GeoDa"
        assert result.routing_path == "spatial_statistics_geoda"

    def test_remote_sensing_routes_to_grass(self, catalog: GISEngineCatalog) -> None:
        workload = SpatialWorkloadProfile(
            geometry_type="satellite_multispectral",
            domain="remote_sensing",
            analysis="spectral_classification",
            data_formats=("GeoTIFF",),
        )
        result = catalog.route_workload(workload)
        assert result.primary.engine.name == "GRASS GIS"
        assert result.routing_path == "remote_sensing_grass_gis"
        assert "NASA" in result.rationale or "350+" in result.rationale

    def test_field_survey_routes_to_gvsig_mobile(self, catalog: GISEngineCatalog) -> None:
        workload = SpatialWorkloadProfile(
            geometry_type="vector_polygon",
            domain="field_survey",
            needs_mobile=True,
            output_type="mobile_gps",
        )
        result = catalog.route_workload(workload)
        assert result.primary.engine.name == "gvSIG"
        assert result.routing_path == "field_survey_gvsig_mobile"

    def test_watershed_routes_to_mapwindow_taudem(self, catalog: GISEngineCatalog) -> None:
        workload = SpatialWorkloadProfile(
            geometry_type="raster_dem",
            domain="watershed_delineation",
            sector="epa_basins",
        )
        result = catalog.route_workload(workload)
        assert result.primary.engine.name == "MapWindow 5"
        assert result.routing_path == "watershed_delineation_mapwindow"

    def test_biodiversity_routes_to_divagis(self, catalog: GISEngineCatalog) -> None:
        workload = SpatialWorkloadProfile(
            geometry_type="tabular_coordinates",
            domain="biodiversity",
            analysis="species_distribution",
        )
        result = catalog.route_workload(workload)
        assert result.primary.engine.name == "Diva GIS"
        assert result.routing_path == "biodiversity_diva_gis"

    def test_defense_sector_raises_restricted(self) -> None:
        with pytest.raises(FalconViewRestrictedDomainError):
            SpatialWorkloadProfile(
                geometry_type="vector_polygon",
                domain="combat_flight_planning",
                sector="defense_restricted",
            )


@pytest.mark.unit
class TestPipelineAndTopologySafety:
    """Verify CRS projection guardrails and geometry topology auditing."""

    def test_crs_safety_no_epsg4326_before_metric_op(self) -> None:
        # Buffer operation on unprojected EPSG:4326 must raise CRSProjectionError
        with pytest.raises(CRSProjectionError):
            SpatialPipelineStep(
                step_id=1,
                operation="buffer",
                engine="qgis",
                input_crs="EPSG:4326",
                output_crs="EPSG:4326",
                input_format="GeoPackage",
                output_format="GeoPackage",
            )

        # Valid pipeline with explicit reprojection first
        step1 = SpatialPipelineStep(
            step_id=1,
            operation="reproject",
            engine="qgis",
            input_crs="EPSG:4326",
            output_crs="EPSG:32632",
            input_format="GeoPackage",
            output_format="GeoPackage",
        )
        step2 = SpatialPipelineStep(
            step_id=2,
            operation="buffer",
            engine="qgis",
            input_crs="EPSG:32632",
            output_crs="EPSG:32632",
            input_format="GeoPackage",
            output_format="GeoPackage",
        )
        dag = SpatialPipelineDAG(steps=(step1, step2), total_steps=2)
        assert dag.total_steps == 2

    def test_topology_audit_critical_on_self_intersections(self) -> None:
        features = [
            {
                "type": "Feature",
                "_mock_self_intersection": True,
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0.0, 0.0], [10.0, 10.0], [10.0, 0.0], [0.0, 10.0], [0.0, 0.0]]],
                },
                "properties": {"area_m2": 0.01},
            }
        ]
        report = audit_polygon_rings(features, sliver_threshold_m2=0.05)
        assert report.is_valid is False
        assert report.severity == "CRITICAL"
        assert report.self_intersection_count >= 1
        assert report.sliver_count >= 1

    def test_zero_fork_config_precedence(self) -> None:
        config_path = SKILL_ROOT / "config.default.yaml"
        assert config_path.exists()
        cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert "operational_budgets" in cfg
        assert cfg["operational_budgets"]["max_raster_memory_mb"] == 4096
        assert cfg["coordinate_reference_systems"]["default_geographic"] == "EPSG:4326"
        assert "FalconView" in cfg["domain_gates"]["defense_restricted_engines"]

    def test_engine_matrix_schema_completeness(self) -> None:
        matrix_path = SKILL_ROOT / "resources" / "gis_engine_matrix.json"
        assert matrix_path.exists()
        data = json.loads(matrix_path.read_text(encoding="utf-8"))
        assert len(data) == 14, f"Expected 14 engines, got {len(data)}"
        for item in data:
            assert "name" in item
            assert "star_rating" in item
            assert "license" in item
            assert "maturity" in item
            assert "primary_domains" in item
            assert "article_note" in item

    def test_scripts_no_input_calls(self) -> None:
        """Rule 42: AST inspection ensuring zero interactive input() calls."""
        scripts_dir = SKILL_ROOT / "scripts"
        py_files = list(scripts_dir.glob("*.py"))
        assert len(py_files) >= 4

        for py_file in py_files:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    assert node.func.id != "input", f"Forbidden input() call detected in {py_file.name}"


@pytest.mark.unit
class TestSkillCraftHygiene:
    """Verify open-source-gis-architect passes SkillValidator and SkillCardParser."""

    @pytest.mark.asyncio
    async def test_skill_validation_pipeline(self) -> None:
        report = await SkillValidator.validate_async(SKILL_ROOT)
        assert report.valid is True, f"Skill craft validation failed: {report.errors}"

    def test_skill_card_parser(self) -> None:
        discovered = SkillCardParser.scan_root(SKILL_ROOT.parent)
        assert "open-source-gis-architect" in discovered
        node = discovered["open-source-gis-architect"]
        assert len(node.stages) == 5
        assert len(node.anti_patterns) >= 6
        assert len(node.invariants) >= 5
        assert all(inv.is_blocking for inv in node.invariants)
