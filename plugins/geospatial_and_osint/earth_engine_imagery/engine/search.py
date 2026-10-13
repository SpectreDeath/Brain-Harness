"""Image collection discovery and metadata inspection mixin."""

from __future__ import annotations

from typing import Any
import structlog

from plugins.geospatial_and_osint.earth_engine_imagery.engine.core import BaseEarthEngine, ee

logger = structlog.get_logger(__name__)


class ImageSearchMixin(BaseEarthEngine):
    """Provides satellite image collection search, filtering, and structural description."""

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
        if not collection_id:
            return {"status": "error", "error": "collection_id is required"}

        box = bbox if bbox and len(bbox) == 4 else [-122.5, 37.7, -122.3, 37.9]

        if self._ensure_initialized() and ee is not None:
            try:
                geom = ee.Geometry.Rectangle(box)
                col = (
                    ee.ImageCollection(collection_id)
                    .filterBounds(geom)
                    .filterDate(start_date, end_date)
                    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud_cover))
                    .limit(limit)
                )
                info = col.getInfo()
                features = info.get("features", [])
                scenes = [
                    {
                        "id": f.get("id"),
                        "date": f.get("properties", {}).get("system:time_start"),
                        "cloud_cover": f.get("properties", {}).get("CLOUDY_PIXEL_PERCENTAGE", 0.0),
                        "bands": [b.get("id") for b in f.get("bands", [])],
                    }
                    for f in features
                ]
                return {
                    "status": "ok",
                    "mode": "live",
                    "collection_id": collection_id,
                    "bbox": box,
                    "date_range": [start_date, end_date],
                    "total_found": len(scenes),
                    "scenes": scenes,
                }
            except Exception as e:
                logger.warning("live_ee_search_failed_falling_back", error=str(e))

        # High-fidelity offline simulation
        scenes = []
        base_name = collection_id.split("/")[-1]
        for i in range(min(limit, 5)):
            day_offset = i * 5 + 1
            dt = f"2026-04-{day_offset:02d}"
            cloud_pct = round(2.5 + (i * 3.1) % (max_cloud_cover or 20.0), 2)
            scenes.append(
                {
                    "id": f"{collection_id}/{base_name}_202604{day_offset:02d}T183921",
                    "date": dt,
                    "cloud_cover_percentage": cloud_pct,
                    "crs": "EPSG:32610",
                    "bands": ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B9", "B11", "B12"],
                    "resolution_meters": 10.0 if "S2" in collection_id else 30.0,
                }
            )

        return {
            "status": "ok",
            "mode": "simulation",
            "collection_id": collection_id,
            "bbox": box,
            "date_range": [start_date, end_date],
            "max_cloud_cover": max_cloud_cover,
            "total_found": len(scenes),
            "scenes": scenes,
        }

    def describe_image(self, image_id: str) -> dict[str, Any]:
        """Extract image properties, band definitions, spatial resolution, and CRS projection."""
        if not image_id:
            return {"status": "error", "error": "image_id is required"}

        if self._ensure_initialized() and ee is not None:
            try:
                img = ee.Image(image_id)
                info = img.getInfo()
                return {
                    "status": "ok",
                    "mode": "live",
                    "image_id": image_id,
                    "properties": info.get("properties", {}),
                    "bands": [b.get("id") for b in info.get("bands", [])],
                }
            except Exception as e:
                logger.warning("live_ee_describe_failed_falling_back", error=str(e))

        is_s2 = "S2" in image_id.upper()
        bands = (
            ["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B9", "B11", "B12", "QA60"]
            if is_s2
            else ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7", "QA_PIXEL"]
        )
        return {
            "status": "ok",
            "mode": "simulation",
            "image_id": image_id,
            "type": "Image",
            "bands_count": len(bands),
            "bands": bands,
            "spatial_resolution_meters": 10.0 if is_s2 else 30.0,
            "crs": "EPSG:32610",
            "sensor": "MSI" if is_s2 else "OLI/TIRS",
            "spacecraft": "Sentinel-2B" if is_s2 else "Landsat-8",
            "radiometric_resolution_bits": 12 if is_s2 else 16,
        }
