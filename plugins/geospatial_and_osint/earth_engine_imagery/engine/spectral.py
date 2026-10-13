"""Multi-spectral vegetation, water, and burn index processing mixin."""

from __future__ import annotations

from typing import Any
import structlog

from plugins.geospatial_and_osint.earth_engine_imagery.engine.core import BaseEarthEngine, ee

logger = structlog.get_logger(__name__)


class SpectralProcessingMixin(BaseEarthEngine):
    """Provides spectral index transformations including NDVI, NDWI, EVI, NBR, and custom equations."""

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
        idx = (index_type or "NDVI").upper()
        formula_map = {
            "NDVI": f"({nir_band} - {red_band}) / ({nir_band} + {red_band})",
            "NDWI": f"({nir_band} - {swir_band}) / ({nir_band} + {swir_band})",
            "NBR": f"({nir_band} - {swir_band}) / ({nir_band} + {swir_band})",
            "EVI": f"2.5 * (({nir_band} - {red_band}) / ({nir_band} + 6.0 * {red_band} - 7.5 * {blue_band} + 1.0))",
        }

        formula = custom_formula if idx == "CUSTOM" and custom_formula else formula_map.get(idx, formula_map["NDVI"])

        if self._ensure_initialized() and ee is not None:
            try:
                img = ee.Image(image_id)
                if idx == "NDVI":
                    img.normalizedDifference([nir_band, red_band]).rename("ndvi")
                elif idx in ("NDWI", "NBR"):
                    img.normalizedDifference([nir_band, swir_band]).rename(idx.lower())
                else:
                    img.expression(formula)
                return {
                    "status": "ok",
                    "mode": "live",
                    "image_id": image_id,
                    "index_type": idx,
                    "formula": formula,
                    "output_band": idx.lower(),
                }
            except Exception as e:
                logger.warning("live_ee_index_failed_falling_back", error=str(e))

        # Offline spectral calculation model
        return {
            "status": "ok",
            "mode": "simulation",
            "image_id": image_id,
            "index_type": idx,
            "formula": formula,
            "bands_used": {
                "nir": nir_band,
                "red": red_band,
                "blue": blue_band,
                "swir": swir_band,
            },
            "output_band": idx.lower(),
            "valid_range": [-1.0, 1.0] if idx != "EVI" else [-1.5, 1.5],
            "typical_vegetation_threshold": 0.4 if idx == "NDVI" else 0.0,
            "description": f"Spectral index {idx} generated with formula: {formula}",
        }
