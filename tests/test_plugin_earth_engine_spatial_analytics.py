"""Tests for Google Earth Engine Spatial Analytics Plugin."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.creator.validator import PluginValidator
from plugins.geospatial_and_osint.earth_engine_imagery.main import (
    EARTH_ENGINE_IMAGERY_KEY,
    EarthEngineImageryPlugin,
)
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.main import (
    EARTH_ENGINE_SPATIAL_ANALYTICS_KEY,
    EarthEngineSpatialAnalyticsPlugin,
    EarthEngineSpatialAnalyticsService,
    ee_analyze_terrain,
    ee_manage_batch_task,
    ee_query_data_catalog,
    ee_vector_spatial_query,
    ee_zonal_statistics,
)


@pytest.fixture
def plugin_dir() -> Path:
    target = Path(__file__).parent.parent / "plugins" / "geospatial_and_osint" / "earth_engine_spatial_analytics"
    assert target.exists(), f"Plugin directory missing: {target}"
    return target


@pytest.mark.unit
class TestEarthEngineSpatialAnalyticsPlugin:
    """Unit and lifecycle test suite for Earth Engine vector spatial analytics & catalog plugin."""

    @pytest.mark.asyncio
    async def test_plugin_ioc_lifecycle(self) -> None:
        """Verify plugin registers typed ServiceKey and declares dependency on imagery plugin."""
        ctx = ServiceContext()
        img_plugin = EarthEngineImageryPlugin()
        ana_plugin = EarthEngineSpatialAnalyticsPlugin()

        assert ana_plugin.name == "plugin.earth_engine_spatial_analytics"
        assert EARTH_ENGINE_SPATIAL_ANALYTICS_KEY in ana_plugin.provides
        assert EARTH_ENGINE_IMAGERY_KEY in ana_plugin.requires

        await img_plugin.on_load(ctx)
        await ana_plugin.on_load(ctx)

        svc = ctx.require(EARTH_ENGINE_SPATIAL_ANALYTICS_KEY)
        assert isinstance(svc, EarthEngineSpatialAnalyticsService)

        await ana_plugin.on_enable()
        await ana_plugin.on_disable()
        await ana_plugin.on_unload()

    def test_zonal_statistics_polygon(self) -> None:
        """Verify zonal reduction statistics over a GeoJSON polygon boundary."""
        field_poly = {
            "type": "Polygon",
            "coordinates": [[
                [-122.5, 37.7],
                [-122.3, 37.7],
                [-122.3, 37.9],
                [-122.5, 37.9],
                [-122.5, 37.7],
            ]],
        }

        res = ee_zonal_statistics(
            image_id="COPERNICUS/S2_SR_HARMONIZED/20260401",
            geometry_geojson=field_poly,
            reducer="mean",
            scale_meters=30.0,
            bands=["B4", "B8"],
        )

        assert res["status"] == "ok"
        assert res["reducer"] == "mean"
        assert "statistics" in res
        stats = res["statistics"]
        assert "B4" in stats
        assert "B8" in stats

    def test_analyze_terrain_dem(self) -> None:
        """Verify digital elevation model topographic calculations (slope, aspect, hillshade)."""
        res = ee_analyze_terrain(
            dem_asset="USGS/3DEP/10m",
            bbox=[-122.5, 37.7, -122.3, 37.9],
            compute_slope=True,
            compute_aspect=True,
            compute_hillshade=True,
        )

        assert res["status"] == "ok"
        assert res["dem_asset"] == "USGS/3DEP/10m"
        metrics = res["terrain_metrics"]
        assert "elevation_mean_meters" in metrics
        assert "slope_mean_degrees" in metrics
        assert "dominant_aspect_degrees" in metrics
        assert "hillshade_mean_illumination" in metrics

    def test_vector_spatial_query(self) -> None:
        """Verify vector feature filtering and attribute querying."""
        res = ee_vector_spatial_query(
            table_asset="TIGER/2018/States",
            filter_property="NAME",
            filter_value="California",
            limit=5,
        )

        assert res["status"] == "ok"
        assert res["table_asset"] == "TIGER/2018/States"
        assert res["features_count"] > 0
        feat = res["features"][0]
        assert "properties" in feat

    def test_query_data_catalog(self) -> None:
        """Verify searching the public Earth Engine Data Catalog by query and category."""
        # Query by topic
        cat_res = ee_query_data_catalog(query="sentinel", limit=5)
        assert cat_res["status"] == "ok"
        assert cat_res["total_found"] > 0
        assert any("sentinel" in (ds["id"] + " " + ds["title"] + " " + " ".join(ds.get("tags", []))).lower() for ds in cat_res["datasets"])

        # Query by category
        elev_res = ee_query_data_catalog(category="elevation", limit=5)
        assert elev_res["status"] == "ok"
        assert elev_res["total_found"] > 0
        assert all(ds["category"] == "elevation" for ds in elev_res["datasets"])

    def test_manage_batch_task(self) -> None:
        """Verify task management actions (list, status, cancel)."""
        # List tasks
        list_res = ee_manage_batch_task(action="list", limit=5)
        assert list_res["status"] == "ok"
        assert "tasks" in list_res

        # Status inspection
        stat_res = ee_manage_batch_task(action="status", task_id="task_ee_export_20260908_001")
        assert stat_res["status"] == "ok"
        assert stat_res["task_id"] == "task_ee_export_20260908_001"
        assert stat_res["state"] == "COMPLETED"

        # Cancellation
        canc_res = ee_manage_batch_task(action="cancel", task_id="task_ee_export_20260908_002")
        assert canc_res["status"] == "ok"
        assert canc_res["state"] == "CANCEL_REQUESTED"

    @pytest.mark.asyncio
    async def test_plugin_validator_compliance(self, plugin_dir: Path) -> None:
        """Verify plugin passes 100% of PluginValidator pre-flight rules."""
        report = await PluginValidator.validate(plugin_dir, dry_run=False)
        assert report.valid is True, f"PluginValidator failed: {report.errors}"
