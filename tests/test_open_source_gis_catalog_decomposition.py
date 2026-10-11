"""Contract tests for Open-Source GIS Catalog architecture decomposition (Cycle 38).

Verifies:
1. Rule 11 submodule line bounds (< 200 lines across all submodules in catalog/)
2. Complete symbol re-exports from harness.services.open_source_gis.catalog facade
3. Fallback engine catalog integrity and domain coverage
4. Default catalog and weight loaders with resource location fallback
5. Isolated routing pathways: environmental, statistical, and vector/web routes
6. GISEngineCatalog coordinator methods, engine lookups, and workload routing
"""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.services.open_source_gis.models import SpatialWorkloadProfile


@pytest.mark.unit
class TestOpenSourceGisCatalogDecompositionContracts:
    """Contract verification for catalog subpackage modularization."""

    def test_rule_11_submodule_line_limits(self) -> None:
        """Verify all submodules in catalog/ remain strictly under 200 lines."""
        catalog_dir = (
            Path(__file__).parent.parent
            / "src"
            / "harness"
            / "services"
            / "open_source_gis"
            / "catalog"
        )
        assert catalog_dir.is_dir(), f"Catalog directory does not exist: {catalog_dir}"

        py_files = list(catalog_dir.glob("*.py"))
        assert len(py_files) >= 7, f"Expected at least 7 submodules, found {len(py_files)}"

        for py_file in py_files:
            line_count = len(py_file.read_text(encoding="utf-8").splitlines())
            assert (
                line_count < 200
            ), f"Rule 11 violation: {py_file.name} has {line_count} lines (must be < 200)"

    def test_facade_re_exports(self) -> None:
        """Verify backward-compatible imports from harness.services.open_source_gis.catalog."""
        from harness.services.open_source_gis.catalog import (
            GISEngineCatalog,
            find_resource_file,
            get_fallback_engine_catalog,
            load_default_catalog,
            load_default_weights,
            route_workload,
            try_environmental_routes,
            try_statistical_routes,
            try_vector_web_routes,
        )

        assert callable(GISEngineCatalog)
        assert callable(find_resource_file)
        assert callable(get_fallback_engine_catalog)
        assert callable(load_default_catalog)
        assert callable(load_default_weights)
        assert callable(route_workload)
        assert callable(try_environmental_routes)
        assert callable(try_statistical_routes)
        assert callable(try_vector_web_routes)

    def test_fallback_engine_catalog_integrity(self) -> None:
        """Verify fallback engine catalog contains core reference engines with valid schemas."""
        from harness.services.open_source_gis.catalog.fallback import (
            get_fallback_engine_catalog,
        )

        engines = get_fallback_engine_catalog()
        assert len(engines) == 8

        expected_fallback_names = {
            "QGIS 3",
            "SAGA GIS",
            "Whitebox GAT",
            "GRASS GIS",
            "GeoDa",
            "gvSIG",
            "MapWindow 5",
            "Diva GIS",
        }
        actual_names = {e.name for e in engines}
        assert actual_names == expected_fallback_names

        for record in engines:
            assert record.name
            assert record.star_rating >= 3.0
            assert record.license
            assert record.maturity in ("production", "mature", "experimental", "maintenance")
            assert len(record.sector_flags) > 0
            assert len(record.primary_domains) > 0
            assert len(record.supported_formats) > 0
            assert record.article_note

    def test_loader_functions(self) -> None:
        """Verify catalog and weight loading handles existing files and fallbacks."""
        from harness.services.open_source_gis.catalog.loader import (
            load_default_catalog,
            load_default_weights,
        )

        catalog_list = load_default_catalog()
        assert len(catalog_list) >= 14
        names = {e.name for e in catalog_list}
        assert "QGIS 3" in names
        assert "Whitebox GAT" in names
        assert "uDig" in names
        assert "OpenJUMP" in names

        weights = load_default_weights()
        assert isinstance(weights, dict)
        assert "analytical_depth" in weights
        assert "cartography" in weights
        assert "specialized_tooling" in weights
        assert "automation_scripting" in weights

    def test_isolated_environmental_routes(self) -> None:
        """Verify specialized environmental workload routes trigger expected recommendations."""
        from harness.services.open_source_gis.catalog.environmental_paths import (
            try_environmental_routes,
        )
        from harness.services.open_source_gis.catalog.loader import load_default_catalog

        engines = {e.name: e for e in load_default_catalog()}

        # LiDAR point cloud workload
        lidar_profile = SpatialWorkloadProfile(
            geometry_type="point_cloud",
            domain="lidar_hydrology",
            data_formats=("LAS", "LAZ"),
            has_lidar=True,
        )
        rec = try_environmental_routes(engines, lidar_profile)
        assert rec is not None
        assert rec.primary.engine.name == "Whitebox GAT"
        assert rec.routing_path == "lidar_hydrology_whitebox_gat"

        # Hydrology / DEM morphometry workload
        hydro_profile = SpatialWorkloadProfile(
            geometry_type="raster_dem",
            domain="terrain_morphometry",
            analysis="twi",
            data_formats=("GeoTIFF",),
        )
        rec = try_environmental_routes(engines, hydro_profile)
        assert rec is not None
        assert rec.primary.engine.name == "SAGA GIS"
        assert rec.routing_path == "terrain_morphometry_saga_gis"

    def test_isolated_statistical_routes(self) -> None:
        """Verify spatial statistical and survey workloads resolve appropriately."""
        from harness.services.open_source_gis.catalog.loader import load_default_catalog
        from harness.services.open_source_gis.catalog.statistical_paths import (
            try_statistical_routes,
        )

        engines = {e.name: e for e in load_default_catalog()}

        # Spatial econometrics / Moran's I
        stat_profile = SpatialWorkloadProfile(
            geometry_type="vector_polygon",
            domain="spatial_statistics",
            needs_statistics=True,
            analysis="moran_i",
            data_formats=("Shapefile",),
        )
        rec = try_statistical_routes(engines, stat_profile)
        assert rec is not None
        assert rec.primary.engine.name == "GeoDa"
        assert rec.routing_path == "spatial_statistics_geoda"

        # Field GPS survey workload
        gps_profile = SpatialWorkloadProfile(
            geometry_type="vector_polygon",
            domain="field_survey",
            needs_mobile=True,
            output_type="mobile_gps",
        )
        rec = try_statistical_routes(engines, gps_profile)
        assert rec is not None
        assert rec.primary.engine.name == "gvSIG"
        assert rec.routing_path == "field_survey_gvsig_mobile"

    def test_isolated_vector_web_routes(self) -> None:
        """Verify web mapping and vector conflation pathways."""
        from harness.services.open_source_gis.catalog.loader import load_default_catalog
        from harness.services.open_source_gis.catalog.vector_web_paths import (
            try_vector_web_routes,
        )

        engines = {e.name: e for e in load_default_catalog()}

        # OGC WMS/WFS web map service
        wms_profile = SpatialWorkloadProfile(
            geometry_type="vector_polygon",
            domain="ogc_web_services",
            data_formats=("WMS", "WFS"),
        )
        rec = try_vector_web_routes(engines, wms_profile)
        assert rec is not None
        assert rec.primary.engine.name == "uDig"
        assert rec.routing_path == "ogc_services_udig"

        # Conflation and topology cleaning
        conflation_profile = SpatialWorkloadProfile(
            geometry_type="vector_polygon",
            domain="cadastral_conflation",
            analysis="cadastral_conflation",
        )
        rec = try_vector_web_routes(engines, conflation_profile)
        assert rec is not None
        assert rec.primary.engine.name == "OpenJUMP"
        assert rec.routing_path == "vector_conflation_openjump"

    def test_gis_engine_catalog_coordinator(self) -> None:
        """Verify GISEngineCatalog initialization, lookups, and full routing dispatch."""
        from harness.services.open_source_gis.catalog import GISEngineCatalog

        cat = GISEngineCatalog()
        assert len(cat.engines) >= 14
        assert cat.get_engine("QGIS 3") is not None
        assert cat.get_engine("non_existent") is None

        # Route via instance
        profile = SpatialWorkloadProfile(
            geometry_type="point_cloud",
            domain="lidar_hydrology",
            data_formats=("LAS", "LAZ"),
            has_lidar=True,
        )
        rec = cat.route_workload(profile)
        assert rec is not None
        assert rec.primary.engine.name == "Whitebox GAT"
        assert rec.routing_path == "lidar_hydrology_whitebox_gat"
