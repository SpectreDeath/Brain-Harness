"""Vector FeatureCollection query, attribute filtering, and spatial bounding operations."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def execute_vector_query(
    table_asset: str,
    filter_property: str = "",
    filter_value: str = "",
    geometry_filter: dict[str, Any] | None = None,
    limit: int = 25,
    ee_initialized: bool = False,
    ee_module: Any = None,
) -> dict[str, Any]:
    """Query and filter vector FeatureCollections (admin boundaries, watersheds, parcels)."""
    if not table_asset:
        return {"status": "error", "error": "table_asset is required"}

    if ee_initialized and ee_module is not None:
        try:
            fc = ee_module.FeatureCollection(table_asset)
            if filter_property and filter_value:
                fc = fc.filter(ee_module.Filter.eq(filter_property, filter_value))
            if geometry_filter:
                fc = fc.filterBounds(ee_module.Geometry(geometry_filter))
            features = fc.limit(limit).getInfo().get("features", [])
            return {
                "status": "ok",
                "mode": "live",
                "table_asset": table_asset,
                "features_count": len(features),
                "features": [
                    {"id": f.get("id"), "properties": f.get("properties", {})}
                    for f in features
                ],
            }
        except Exception as e:
            logger.warning("live_ee_vector_query_failed_falling_back", extra={"error": str(e)})

    # Offline vector feature simulation
    sim_features = [
        {
            "id": f"{table_asset}/feature_{i+1:03d}",
            "properties": {
                filter_property or "NAME": filter_value or f"Zone_{i+1}",
                "CODE": f"REG_{i+1:02d}",
                "AREA_SQKM": round(145.2 + i * 28.5, 2),
                "PERIMETER_KM": round(54.1 + i * 8.2, 2),
            },
            "geometry_type": "Polygon",
        }
        for i in range(min(limit, 5))
    ]

    return {
        "status": "ok",
        "mode": "simulation",
        "table_asset": table_asset,
        "features_count": len(sim_features),
        "features": sim_features,
    }
