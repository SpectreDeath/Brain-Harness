"""Google Earth Engine Satellite Imagery & Spectral Processing Plugin for Brain Harness."""

from __future__ import annotations

from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from plugins.geospatial_and_osint.earth_engine_imagery.engine import (
    EARTH_ENGINE_IMAGERY_KEY,
    EarthEngineImageryEngine,
    EarthEngineImageryService,
    get_default_imagery_engine,
    resolve_earth_engine_imagery,
)

logger = structlog.get_logger(__name__)


# Top-level entrypoint tools
def ee_search_image_collection(
    collection_id: str,
    bbox: list[float] | None = None,
    start_date: str = "2026-01-01",
    end_date: str = "2026-06-01",
    max_cloud_cover: float = 20.0,
    limit: int = 10,
) -> dict[str, Any]:
    """Search satellite collections by spatial bbox, temporal window, and cloud cover."""
    engine = get_default_imagery_engine()
    return engine.search_image_collection(
        collection_id=collection_id,
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover,
        limit=limit,
    )


def ee_compute_spectral_index(
    image_id: str,
    index_type: str = "NDVI",
    nir_band: str = "B8",
    red_band: str = "B4",
    blue_band: str = "B2",
    swir_band: str = "B11",
    custom_formula: str = "",
) -> dict[str, Any]:
    """Compute multi-spectral indices (NDVI, NDWI, EVI, NBR) or custom normalized band equations."""
    engine = get_default_imagery_engine()
    return engine.compute_spectral_index(
        image_id=image_id,
        index_type=index_type,
        nir_band=nir_band,
        red_band=red_band,
        blue_band=blue_band,
        swir_band=swir_band,
        custom_formula=custom_formula,
    )


def ee_composite_timeseries(
    collection_id: str,
    bbox: list[float] | None = None,
    start_date: str = "2026-01-01",
    end_date: str = "2026-06-01",
    composite_method: str = "median",
    mask_clouds: bool = True,
) -> dict[str, Any]:
    """Generate multi-temporal composite reductions with QA cloud masking."""
    engine = get_default_imagery_engine()
    return engine.composite_timeseries(
        collection_id=collection_id,
        bbox=bbox,
        start_date=start_date,
        end_date=end_date,
        composite_method=composite_method,
        mask_clouds=mask_clouds,
    )


def ee_get_image_thumbnail_url(
    image_id: str,
    bands: list[str] | None = None,
    min_val: float = 0.0,
    max_val: float = 3000.0,
    dimensions: int = 512,
    palette: list[str] | None = None,
) -> dict[str, Any]:
    """Generate visual preview thumbnail URLs and map tile metadata."""
    engine = get_default_imagery_engine()
    return engine.get_image_thumbnail_url(
        image_id=image_id,
        bands=bands,
        min_val=min_val,
        max_val=max_val,
        dimensions=dimensions,
        palette=palette,
    )


def ee_describe_image(image_id: str) -> dict[str, Any]:
    """Extract image properties, band definitions, spatial resolution, and CRS projection."""
    engine = get_default_imagery_engine()
    return engine.describe_image(image_id=image_id)


class EarthEngineImageryPlugin(HarnessPlugin):
    """Brain Harness plugin exposing Google Earth Engine satellite imagery services."""

    def __init__(self) -> None:
        super().__init__()
        self._engine = get_default_imagery_engine()

    @property
    def name(self) -> str:
        return "plugin.earth_engine_imagery"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Google Earth Engine satellite imagery querying and spectral index processing plugin."

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [EARTH_ENGINE_IMAGERY_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(EARTH_ENGINE_IMAGERY_KEY, self._engine)
        logger.info("earth_engine_imagery_plugin_loaded")

    async def on_enable(self) -> None:
        logger.info("earth_engine_imagery_plugin_enabled")

    async def on_disable(self) -> None:
        logger.info("earth_engine_imagery_plugin_disabled")

    async def on_unload(self) -> None:
        logger.info("earth_engine_imagery_plugin_unloaded")


plugin = EarthEngineImageryPlugin()

__all__ = [
    "EARTH_ENGINE_IMAGERY_KEY",
    "EarthEngineImageryEngine",
    "EarthEngineImageryPlugin",
    "EarthEngineImageryService",
    "ee_composite_timeseries",
    "ee_compute_spectral_index",
    "ee_describe_image",
    "ee_get_image_thumbnail_url",
    "ee_search_image_collection",
    "get_default_imagery_engine",
    "plugin",
    "resolve_earth_engine_imagery",
]
