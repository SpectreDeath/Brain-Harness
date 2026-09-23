"""Test suite for OpenSourceGisService kernel service and domain models."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.kernel.context import ServiceContext
from harness.services.open_source_gis import (
    OPEN_SOURCE_GIS_SERVICE_KEY,
    DefaultOpenSourceGisService,
    FalconViewRestrictedDomainError,
    OpenSourceGisService,
    SpatialArchitectureReceipt,
    SpatialWorkloadProfile,
)


@pytest.mark.unit
class TestOpenSourceGisServiceProtocol:
    """Verify OpenSourceGisService conforms to runtime_checkable protocol and IoC semantics."""

    def test_service_instance_conforms_to_protocol(self) -> None:
        service = DefaultOpenSourceGisService()
        assert isinstance(service, OpenSourceGisService)

    def test_ioc_context_provision_and_resolution(self) -> None:
        context = ServiceContext()
        service = DefaultOpenSourceGisService()
        context.provide(OPEN_SOURCE_GIS_SERVICE_KEY, service)

        resolved = context.require(OPEN_SOURCE_GIS_SERVICE_KEY)
        assert resolved is service
        assert isinstance(resolved, OpenSourceGisService)


@pytest.mark.unit
class TestDeterministicRoutingPaths:
    """Verify deterministic routing across 14 engines via the service seam."""

    @pytest.fixture
    def service(self) -> OpenSourceGisService:
        return DefaultOpenSourceGisService()

    def test_lidar_routing(self, service: OpenSourceGisService) -> None:
        profile = SpatialWorkloadProfile(
            geometry_type="point_cloud",
            domain="lidar_hydrology",
            data_formats=("LAS", "LAZ"),
            has_lidar=True,
        )
        res = service.route_workload(profile)
        assert res.primary.engine.name == "Whitebox GAT"
        assert res.routing_path == "lidar_hydrology_whitebox_gat"
        assert res.primary.fitness_score >= 0.95
        assert res.secondary is not None
        assert res.secondary.engine.name == "SAGA GIS"

    def test_terrain_morphometry_routing(self, service: OpenSourceGisService) -> None:
        profile = SpatialWorkloadProfile(
            geometry_type="raster_dem",
            domain="terrain_morphometry",
            analysis="twi",
            data_formats=("GeoTIFF",),
        )
        res = service.route_workload(profile)
        assert res.primary.engine.name == "SAGA GIS"
        assert res.routing_path == "terrain_morphometry_saga_gis"
        assert "Topographic Wetness Index" in res.rationale

    def test_spatial_statistics_routing(self, service: OpenSourceGisService) -> None:
        profile = SpatialWorkloadProfile(
            geometry_type="vector_polygon",
            domain="spatial_statistics",
            needs_statistics=True,
            analysis="moran_i",
        )
        res = service.route_workload(profile)
        assert res.primary.engine.name == "GeoDa"
        assert res.routing_path == "spatial_statistics_geoda"

    def test_remote_sensing_routing(self, service: OpenSourceGisService) -> None:
        profile = SpatialWorkloadProfile(
            geometry_type="satellite_multispectral",
            domain="remote_sensing",
            analysis="spectral_classification",
        )
        res = service.route_workload(profile)
        assert res.primary.engine.name == "GRASS GIS"
        assert res.routing_path == "remote_sensing_grass_gis"

    def test_field_survey_routing(self, service: OpenSourceGisService) -> None:
        profile = SpatialWorkloadProfile(
            geometry_type="vector_polygon",
            domain="field_survey",
            needs_mobile=True,
        )
        res = service.route_workload(profile)
        assert res.primary.engine.name == "gvSIG"
        assert res.routing_path == "field_survey_gvsig_mobile"

    def test_watershed_delineation_routing(self, service: OpenSourceGisService) -> None:
        profile = SpatialWorkloadProfile(
            geometry_type="raster_dem",
            domain="watershed_delineation",
            sector="epa_basins",
        )
        res = service.route_workload(profile)
        assert res.primary.engine.name == "MapWindow 5"
        assert res.routing_path == "watershed_delineation_mapwindow"

    def test_biodiversity_routing(self, service: OpenSourceGisService) -> None:
        profile = SpatialWorkloadProfile(
            geometry_type="tabular_coordinates",
            domain="biodiversity",
            analysis="species_distribution",
        )
        res = service.route_workload(profile)
        assert res.primary.engine.name == "Diva GIS"
        assert res.routing_path == "biodiversity_diva_gis"

    def test_urban_acoustics_routing(self, service: OpenSourceGisService) -> None:
        profile = SpatialWorkloadProfile(
            geometry_type="vector_polygon",
            domain="urban_acoustics",
            analysis="noise_mapping",
        )
        res = service.route_workload(profile)
        assert res.primary.engine.name == "OrbisGIS"
        assert res.routing_path == "urban_acoustics_orbisgis"

    def test_ogc_web_services_routing(self, service: OpenSourceGisService) -> None:
        profile = SpatialWorkloadProfile(
            geometry_type="vector_polygon",
            domain="ogc_web_services",
            data_formats=("WMS", "WFS"),
        )
        res = service.route_workload(profile)
        assert res.primary.engine.name == "uDig"
        assert res.routing_path == "ogc_services_udig"

    def test_vector_conflation_routing(self, service: OpenSourceGisService) -> None:
        profile = SpatialWorkloadProfile(
            geometry_type="vector_polygon",
            domain="vector_conflation",
            analysis="conflation",
        )
        res = service.route_workload(profile)
        assert res.primary.engine.name == "OpenJUMP"
        assert res.routing_path == "vector_conflation_openjump"

    def test_land_water_management_routing(self, service: OpenSourceGisService) -> None:
        profile = SpatialWorkloadProfile(
            geometry_type="raster_dem",
            domain="land_water_management",
            has_time_series=True,
        )
        res = service.route_workload(profile)
        assert res.primary.engine.name == "ILWIS"
        assert res.routing_path == "land_water_management_ilwis"

    def test_general_gis_fallback_routing(self, service: OpenSourceGisService) -> None:
        profile = SpatialWorkloadProfile(
            geometry_type="vector_polygon",
            domain="general_gis",
        )
        res = service.route_workload(profile)
        assert res.primary.engine.name == "QGIS 3"
        assert res.routing_path == "cartography_qgis3"
        assert res.primary.fitness_score >= 0.95

    def test_defense_sector_halt(self) -> None:
        with pytest.raises(FalconViewRestrictedDomainError):
            SpatialWorkloadProfile(
                geometry_type="vector_polygon",
                domain="defense_flight_planning",
                sector="defense_restricted",
            )


@pytest.mark.unit
class TestPipelineAndTopologyValidation:
    """Verify CRS planar projection safety and geometry topology auditing."""

    @pytest.fixture
    def service(self) -> OpenSourceGisService:
        return DefaultOpenSourceGisService()

    def test_valid_pipeline_with_reprojection(self, service: OpenSourceGisService) -> None:
        steps = [
            {
                "step_id": 1,
                "operation": "reproject",
                "engine": "qgis",
                "input_crs": "EPSG:4326",
                "output_crs": "EPSG:32632",
                "input_format": "GeoPackage",
                "output_format": "GeoPackage",
            },
            {
                "step_id": 2,
                "operation": "buffer",
                "engine": "qgis",
                "input_crs": "EPSG:32632",
                "output_crs": "EPSG:32632",
                "input_format": "GeoPackage",
                "output_format": "GeoPackage",
            },
        ]
        valid, msgs, dag = service.validate_pipeline_dag(steps)
        assert valid is True
        assert len(msgs) == 1
        assert dag is not None
        assert dag.total_steps == 2

    def test_invalid_pipeline_crs_violation(self, service: OpenSourceGisService) -> None:
        steps = [
            {
                "step_id": 1,
                "operation": "buffer",
                "engine": "qgis",
                "input_crs": "EPSG:4326",
                "output_crs": "EPSG:4326",
                "input_format": "GeoPackage",
                "output_format": "GeoPackage",
            }
        ]
        valid, msgs, dag = service.validate_pipeline_dag(steps)
        assert valid is False
        assert dag is None
        assert any("CRS Invariant Violation" in m for m in msgs)

    def test_topology_auditing(self, service: OpenSourceGisService) -> None:
        clean_features = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [0.0, 5.0], [0.0, 0.0]]],
                },
                "properties": {"area_m2": 25.0},
            }
        ]
        report = service.audit_topology(clean_features)
        assert report.is_valid is True
        assert report.severity == "OK"
        assert report.sliver_count == 0

        invalid_features = [
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
        bad_report = service.audit_topology(invalid_features, sliver_threshold_m2=0.05)
        assert bad_report.is_valid is False
        assert bad_report.severity == "CRITICAL"
        assert bad_report.self_intersection_count == 1
        assert bad_report.sliver_count == 1


@pytest.mark.unit
class TestVisualBriefAndArchitectWorkload:
    """Verify Stage 5 HTML visual brief generator and composite architect_workload seam."""

    @pytest.fixture
    def service(self) -> OpenSourceGisService:
        return DefaultOpenSourceGisService()

    def test_generate_visual_brief(self, service: OpenSourceGisService, tmp_path: Path) -> None:
        profile = SpatialWorkloadProfile(
            geometry_type="raster_dem",
            domain="terrain_morphometry",
            analysis="twi",
            data_formats=("GeoTIFF",),
        )
        selection = service.route_workload(profile)
        brief_file = tmp_path / "test-brief.html"

        brief_res = service.generate_visual_brief(
            profile=profile,
            selection=selection,
            output_path=brief_file,
        )
        assert brief_file.exists()
        assert brief_res.report_path == str(brief_file)
        assert brief_res.rendered_nodes >= 2
        content = brief_file.read_text(encoding="utf-8")
        assert "SAGA GIS" in content
        assert "flowchart LR" in content
        assert "Spatial Architecture Decision Brief" in content

    def test_composite_architect_workload(self, service: OpenSourceGisService) -> None:
        profile_data = {
            "geometry_type": "point_cloud",
            "domain": "lidar_hydrology",
            "data_formats": ["LAS", "LAZ"],
            "has_lidar": True,
        }
        steps = [
            {
                "step_id": 1,
                "operation": "reproject",
                "engine": "whitebox",
                "input_crs": "EPSG:4326",
                "output_crs": "EPSG:32632",
                "input_format": "LAS",
                "output_format": "LAS",
            }
        ]
        receipt = service.architect_workload(
            profile_data=profile_data,
            pipeline_steps=steps,
            generate_brief=True,
        )
        assert isinstance(receipt, SpatialArchitectureReceipt)
        assert receipt.primary_engine == "Whitebox GAT"
        assert receipt.primary_fitness >= 0.95
        assert receipt.pipeline_valid is True
        assert receipt.pipeline_step_count == 1
        assert receipt.visual_brief_path is not None
        assert Path(receipt.visual_brief_path).exists()
        assert "Whitebox GAT" in receipt.receipt_markdown
