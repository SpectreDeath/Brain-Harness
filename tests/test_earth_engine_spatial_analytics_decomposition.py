"""Characterization test contracts for Earth Engine Spatial Analytics decomposition (Cycle 39).

Verifies:
1. Rule 11 submodule line limits (< 200 lines across main.py and engine/)
2. Backward-compatible facade re-exports and subpackage imports
3. Rule 12 & Rule 43 slotted and frozen dataclass immutability
4. Rule 58 single-seam IoC resolver factory resolve_earth_engine_spatial_analytics
5. Isolated domain handler execution (zonal, terrain, vector, catalog, tasks)
6. Plugin lifecycle and Rule 45 module singleton conformance
"""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from plugins.geospatial_and_osint.earth_engine_imagery.main import EARTH_ENGINE_IMAGERY_KEY


@pytest.mark.unit
class TestEarthEngineSpatialAnalyticsDecompositionContracts:
    """Contract verification for Earth Engine spatial analytics decomposition."""

    def test_rule_11_submodule_line_limits(self) -> None:
        """Verify all submodules in engine/ and main.py remain strictly under 200 lines."""
        plugin_root = (
            Path(__file__).parent.parent
            / "plugins"
            / "geospatial_and_osint"
            / "earth_engine_spatial_analytics"
        )
        assert plugin_root.is_dir(), f"Plugin root directory missing: {plugin_root}"

        main_py = plugin_root / "main.py"
        assert main_py.exists(), "main.py missing"
        main_lines = len(main_py.read_text(encoding="utf-8").splitlines())
        assert (
            main_lines < 200
        ), f"Rule 11 violation in main.py: {main_lines} lines (must be < 200)"

        engine_dir = plugin_root / "engine"
        assert engine_dir.is_dir(), f"engine subpackage missing: {engine_dir}"

        py_files = list(engine_dir.glob("*.py"))
        assert len(py_files) >= 8, f"Expected at least 8 submodules in engine/, found {len(py_files)}"

        for py_file in py_files:
            lines = len(py_file.read_text(encoding="utf-8").splitlines())
            assert (
                lines < 200
            ), f"Rule 11 violation in {py_file.name}: {lines} lines (must be < 200)"

    def test_facade_and_submodule_exports(self) -> None:
        """Verify symbols can be imported from main facade and dedicated engine submodules."""
        from plugins.geospatial_and_osint.earth_engine_spatial_analytics.main import (
            EARTH_ENGINE_SPATIAL_ANALYTICS_KEY,
            EarthEngineSpatialAnalyticsEngine,
            EarthEngineSpatialAnalyticsPlugin,
            EarthEngineSpatialAnalyticsService,
            ee_analyze_terrain,
            ee_manage_batch_task,
            ee_query_data_catalog,
            ee_vector_spatial_query,
            ee_zonal_statistics,
            plugin,
            resolve_earth_engine_spatial_analytics,
        )
        from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine import (
            CatalogDataset,
            ZonalStatsRequest,
            compute_terrain_metrics,
            compute_zonal_statistics,
            execute_vector_query,
            manage_tasks,
            query_data_catalog,
        )

        assert EARTH_ENGINE_SPATIAL_ANALYTICS_KEY is not None
        assert callable(EarthEngineSpatialAnalyticsEngine)
        assert callable(EarthEngineSpatialAnalyticsPlugin)
        assert callable(resolve_earth_engine_spatial_analytics)
        assert isinstance(plugin, EarthEngineSpatialAnalyticsPlugin)

        assert callable(ee_zonal_statistics)
        assert callable(ee_analyze_terrain)
        assert callable(ee_vector_spatial_query)
        assert callable(ee_query_data_catalog)
        assert callable(ee_manage_batch_task)

        assert callable(compute_zonal_statistics)
        assert callable(compute_terrain_metrics)
        assert callable(execute_vector_query)
        assert callable(query_data_catalog)
        assert callable(manage_tasks)

    def test_slotted_frozen_dataclass_immutability(self) -> None:
        """Verify Rule 12 & Rule 43 slotted and frozen immutability assertions."""
        from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.models import (
            CatalogDataset,
            ZonalStatsRequest,
        )

        dataset = CatalogDataset(
            dataset_id="TEST/DATASET/001",
            title="Test Dataset",
            category="elevation",
            tags=("test", "elevation"),
            spatial_resolution_meters=10.0,
            time_start="2026-01-01",
            description="Test elevation dataset",
        )
        with pytest.raises((AttributeError, TypeError)):
            dataset.title = "Mutated"  # type: ignore

        req = ZonalStatsRequest(
            image_id="TEST/IMAGE/001",
            geometry_type="Polygon",
            reducer="mean",
            scale_meters=30.0,
            bands=("B4", "B8"),
        )
        with pytest.raises((AttributeError, TypeError)):
            req.reducer = "sum"  # type: ignore

    def test_single_seam_resolver_fallback_and_ioc(self) -> None:
        """Verify Rule 58 single-seam IoC resolution with fallback."""
        from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.models import (
            EARTH_ENGINE_SPATIAL_ANALYTICS_KEY,
            EarthEngineSpatialAnalyticsService,
        )
        from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.resolvers import (
            get_default_spatial_engine,
            resolve_earth_engine_spatial_analytics,
        )

        # 1. No context provided -> default singleton
        default_svc = resolve_earth_engine_spatial_analytics(None)
        assert default_svc is get_default_spatial_engine()

        # 2. Empty context provided -> falls back to default singleton
        empty_ctx = ServiceContext()
        resolved_fallback = resolve_earth_engine_spatial_analytics(empty_ctx)
        assert resolved_fallback is get_default_spatial_engine()

        # 3. Context with custom provider -> resolves custom provider
        custom_ctx = ServiceContext()
        custom_engine = get_default_spatial_engine()
        custom_ctx.provide(EARTH_ENGINE_SPATIAL_ANALYTICS_KEY, custom_engine)
        resolved_custom = resolve_earth_engine_spatial_analytics(custom_ctx)
        assert resolved_custom is custom_engine

    def test_isolated_zonal_statistics(self) -> None:
        """Verify zonal reduction operation across various reduction operators."""
        from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.zonal import (
            compute_zonal_statistics,
        )

        poly = {
            "type": "Polygon",
            "coordinates": [[
                [-122.5, 37.7],
                [-122.3, 37.7],
                [-122.3, 37.9],
                [-122.5, 37.9],
                [-122.5, 37.7],
            ]],
        }

        # Test mean, sum, min, max, stddev
        for red in ("mean", "sum", "min", "max", "stddev"):
            res = compute_zonal_statistics(
                image_id="COPERNICUS/S2_SR_HARMONIZED/test",
                geometry_geojson=poly,
                reducer=red,
                scale_meters=20.0,
                bands=["B4", "B8"],
            )
            assert res["status"] == "ok"
            assert res["reducer"] == red
            assert "statistics" in res
            assert "B4" in res["statistics"]
            assert "B8" in res["statistics"]

    def test_isolated_terrain_metrics(self) -> None:
        """Verify topographic DEM analysis."""
        from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.terrain import (
            compute_terrain_metrics,
        )

        res = compute_terrain_metrics(
            dem_asset="USGS/3DEP/10m",
            bbox=[-122.5, 37.7, -122.3, 37.9],
            compute_slope=True,
            compute_aspect=True,
            compute_hillshade=True,
        )
        assert res["status"] == "ok"
        metrics = res["terrain_metrics"]
        assert "elevation_mean_meters" in metrics
        assert "slope_mean_degrees" in metrics
        assert "dominant_aspect_degrees" in metrics
        assert "hillshade_mean_illumination" in metrics

    def test_isolated_vector_and_catalog(self) -> None:
        """Verify vector FeatureCollection queries and data catalog search."""
        from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.catalog import (
            query_data_catalog,
        )
        from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.vector import (
            execute_vector_query,
        )

        # Vector query
        v_res = execute_vector_query(
            table_asset="TIGER/2018/Counties",
            filter_property="STATEFP",
            filter_value="06",
            limit=5,
        )
        assert v_res["status"] == "ok"
        assert v_res["features_count"] > 0
        assert len(v_res["features"]) <= 5

        # Catalog search
        c_res = query_data_catalog(
            query="elevation",
            category="elevation",
            tags=["dem"],
            limit=5,
        )
        assert c_res["status"] == "ok"
        assert c_res["total_found"] > 0
        for ds in c_res["datasets"]:
            assert ds["category"] == "elevation"

    def test_plugin_lifecycle_and_singleton(self) -> None:
        """Verify plugin lifecycle methods and module singleton."""
        from plugins.geospatial_and_osint.earth_engine_spatial_analytics.main import (
            EARTH_ENGINE_SPATIAL_ANALYTICS_KEY,
            EarthEngineSpatialAnalyticsPlugin,
            plugin,
        )

        assert isinstance(plugin, EarthEngineSpatialAnalyticsPlugin)
        assert plugin.name == "plugin.earth_engine_spatial_analytics"
        assert EARTH_ENGINE_SPATIAL_ANALYTICS_KEY in plugin.provides
        assert EARTH_ENGINE_IMAGERY_KEY in plugin.requires
