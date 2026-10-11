"""Single-seam IoC resolver for Earth Engine Spatial Analytics per AGENTS.md Rule 58."""

from __future__ import annotations

from typing import cast

from harness.kernel.context import ServiceContext
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.core import (
    EarthEngineSpatialAnalyticsEngine,
)
from plugins.geospatial_and_osint.earth_engine_spatial_analytics.engine.models import (
    EARTH_ENGINE_SPATIAL_ANALYTICS_KEY,
    EarthEngineSpatialAnalyticsService,
)

# Process-level default singleton instance
_DEFAULT_SPATIAL_ENGINE: EarthEngineSpatialAnalyticsEngine | None = None


def get_default_spatial_engine() -> EarthEngineSpatialAnalyticsEngine:
    """Obtain or instantiate the process-level default spatial analytics engine."""
    global _DEFAULT_SPATIAL_ENGINE
    if _DEFAULT_SPATIAL_ENGINE is None:
        _DEFAULT_SPATIAL_ENGINE = EarthEngineSpatialAnalyticsEngine()
    return _DEFAULT_SPATIAL_ENGINE


def resolve_earth_engine_spatial_analytics(
    context: ServiceContext | None = None,
) -> EarthEngineSpatialAnalyticsService:
    """Resolve EarthEngineSpatialAnalyticsService from ServiceContext or fallback to process default."""
    if context is not None:
        resolved = context.optional(EARTH_ENGINE_SPATIAL_ANALYTICS_KEY)
        if resolved is not None:
            return cast(EarthEngineSpatialAnalyticsService, resolved)
    return get_default_spatial_engine()
