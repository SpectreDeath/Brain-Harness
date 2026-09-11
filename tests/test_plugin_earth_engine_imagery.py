"""Tests for Google Earth Engine Imagery Plugin."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.creator.validator import PluginValidator
from plugins.geospatial_and_osint.earth_engine_imagery.main import (
    EARTH_ENGINE_IMAGERY_KEY,
    EarthEngineImageryPlugin,
    EarthEngineImageryService,
    ee_composite_timeseries,
    ee_compute_spectral_index,
    ee_describe_image,
    ee_get_image_thumbnail_url,
    ee_search_image_collection,
)


@pytest.fixture
def plugin_dir() -> Path:
    target = Path(__file__).parent.parent / "plugins" / "geospatial_and_osint" / "earth_engine_imagery"
    assert target.exists(), f"Plugin directory missing: {target}"
    return target


@pytest.mark.unit
class TestEarthEngineImageryPlugin:
    """Unit and lifecycle test suite for Earth Engine satellite imagery plugin."""

    @pytest.mark.asyncio
    async def test_plugin_ioc_lifecycle(self) -> None:
        """Verify plugin registers typed ServiceKey into ServiceContext."""
        ctx = ServiceContext()
        plugin = EarthEngineImageryPlugin()

        assert plugin.name == "plugin.earth_engine_imagery"
        assert EARTH_ENGINE_IMAGERY_KEY in plugin.provides

        await plugin.on_load(ctx)
        svc = ctx.require(EARTH_ENGINE_IMAGERY_KEY)
        assert isinstance(svc, EarthEngineImageryService)

        await plugin.on_enable()
        await plugin.on_disable()
        await plugin.on_unload()

    def test_search_image_collection(self) -> None:
        """Verify satellite image collection search with bounding box and date filters."""
        res = ee_search_image_collection(
            collection_id="COPERNICUS/S2_SR_HARMONIZED",
            bbox=[-122.5, 37.7, -122.3, 37.9],
            start_date="2026-03-01",
            end_date="2026-05-01",
            max_cloud_cover=20.0,
            limit=5,
        )
        assert res["status"] == "ok"
        assert res["collection_id"] == "COPERNICUS/S2_SR_HARMONIZED"
        assert res["total_found"] > 0
        assert len(res["scenes"]) <= 5
        first_scene = res["scenes"][0]
        assert "id" in first_scene
        assert "cloud_cover_percentage" in first_scene or "cloud_cover" in first_scene

    def test_compute_spectral_index_ndvi_and_custom(self) -> None:
        """Verify spectral index calculation for standard NDVI and custom band formulas."""
        # Standard NDVI
        ndvi = ee_compute_spectral_index(
            image_id="COPERNICUS/S2_SR_HARMONIZED/20260401",
            index_type="NDVI",
            nir_band="B8",
            red_band="B4",
        )
        assert ndvi["status"] == "ok"
        assert ndvi["index_type"] == "NDVI"
        assert "(B8 - B4) / (B8 + B4)" in ndvi["formula"]
        assert ndvi["output_band"] == "ndvi"

        # Water Index NDWI
        ndwi = ee_compute_spectral_index(
            image_id="COPERNICUS/S2_SR_HARMONIZED/20260401",
            index_type="NDWI",
            nir_band="B8",
            swir_band="B11",
        )
        assert ndwi["status"] == "ok"
        assert ndwi["index_type"] == "NDWI"
        assert ndwi["output_band"] == "ndwi"

        # Custom formula
        custom = ee_compute_spectral_index(
            image_id="LANDSAT/LC08/C02/T1_L2/20260401",
            index_type="CUSTOM",
            custom_formula="(SR_B5 - SR_B4) / (SR_B5 + SR_B4)",
        )
        assert custom["status"] == "ok"
        assert custom["formula"] == "(SR_B5 - SR_B4) / (SR_B5 + SR_B4)"

    def test_composite_timeseries(self) -> None:
        """Verify temporal compositing reductions with QA cloud masking."""
        comp = ee_composite_timeseries(
            collection_id="COPERNICUS/S2_SR_HARMONIZED",
            bbox=[-122.5, 37.7, -122.3, 37.9],
            start_date="2026-01-01",
            end_date="2026-06-01",
            composite_method="median",
            mask_clouds=True,
        )
        assert comp["status"] == "ok"
        assert comp["composite_method"] == "median"
        assert comp["mask_clouds_applied"] is True or comp.get("mask_clouds") is True

    def test_get_image_thumbnail_url(self) -> None:
        """Verify visual preview thumbnail URL generation."""
        thumb = ee_get_image_thumbnail_url(
            image_id="COPERNICUS/S2_SR_HARMONIZED/20260401",
            bands=["B4", "B3", "B2"],
            min_val=0.0,
            max_val=3000.0,
            dimensions=512,
        )
        assert thumb["status"] == "ok"
        assert "thumbnail_url" in thumb
        assert "earthengine.googleapis.com" in thumb["thumbnail_url"]

    def test_describe_image(self) -> None:
        """Verify image metadata inspection and band catalog."""
        desc = ee_describe_image(image_id="COPERNICUS/S2_SR_HARMONIZED/20260401")
        assert desc["status"] == "ok"
        assert desc["image_id"] == "COPERNICUS/S2_SR_HARMONIZED/20260401"
        assert len(desc["bands"]) > 0
        assert "B4" in desc["bands"]
        assert "B8" in desc["bands"]

    @pytest.mark.asyncio
    async def test_plugin_validator_compliance(self, plugin_dir: Path) -> None:
        """Verify plugin passes 100% of PluginValidator pre-flight rules."""
        report = await PluginValidator.validate(plugin_dir, dry_run=False)
        assert report.valid is True, f"PluginValidator failed: {report.errors}"
