"""Protocol definition and typed service key for EarthEngineImageryService."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey


@runtime_checkable
class EarthEngineImageryService(Protocol):
    """Protocol for Earth Engine satellite imagery querying and spectral processing."""

    def search_image_collection(
        self,
        collection_id: str,
        bbox: list[float] | None = None,
        start_date: str = "2026-01-01",
        end_date: str = "2026-06-01",
        max_cloud_cover: float = 20.0,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search satellite collections by spatial bbox, temporal window, and cloud cover."""
        ...

    def compute_spectral_index(
        self,
        image_id: str,
        index_type: str = "NDVI",
        nir_band: str = "B8",
        red_band: str = "B4",
        blue_band: str = "B2",
        swir_band: str = "B11",
        custom_formula: str = "",
    ) -> dict[str, Any]:
        """Compute multi-spectral indices (NDVI, NDWI, EVI, NBR) or custom normalized band equations."""
        ...

    def composite_timeseries(
        self,
        collection_id: str,
        bbox: list[float] | None = None,
        start_date: str = "2026-01-01",
        end_date: str = "2026-06-01",
        composite_method: str = "median",
        mask_clouds: bool = True,
    ) -> dict[str, Any]:
        """Generate multi-temporal composite reductions (median, mean, min, max, greenest pixel)."""
        ...

    def get_image_thumbnail_url(
        self,
        image_id: str,
        bands: list[str] | None = None,
        min_val: float = 0.0,
        max_val: float = 3000.0,
        dimensions: int = 512,
        palette: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate visual preview thumbnail URLs and map tile metadata."""
        ...

    def describe_image(self, image_id: str) -> dict[str, Any]:
        """Extract image properties, band definitions, spatial resolution, and CRS projection."""
        ...


EARTH_ENGINE_IMAGERY_KEY: ServiceKey[EarthEngineImageryService] = ServiceKey("service.earth_engine_imagery")
