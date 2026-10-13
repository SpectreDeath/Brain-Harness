"""Single-seam IoC resolver for Earth Engine Imagery per AGENTS.md Rule 58."""

from __future__ import annotations

from typing import cast

from harness.kernel.context import ServiceContext
from plugins.geospatial_and_osint.earth_engine_imagery.engine.protocols import (
    EARTH_ENGINE_IMAGERY_KEY,
    EarthEngineImageryService,
)
from plugins.geospatial_and_osint.earth_engine_imagery.engine.service import (
    EarthEngineImageryEngine,
)

# Process-level default singleton instance
_DEFAULT_IMAGERY_ENGINE: EarthEngineImageryEngine | None = None


def get_default_imagery_engine() -> EarthEngineImageryEngine:
    """Obtain or instantiate the process-level default imagery engine."""
    global _DEFAULT_IMAGERY_ENGINE
    if _DEFAULT_IMAGERY_ENGINE is None:
        _DEFAULT_IMAGERY_ENGINE = EarthEngineImageryEngine()
    return _DEFAULT_IMAGERY_ENGINE


def resolve_earth_engine_imagery(
    context: ServiceContext | None = None,
) -> EarthEngineImageryService:
    """Resolve EarthEngineImageryService from ServiceContext or fallback to process default."""
    if context is not None:
        resolved = context.optional(EARTH_ENGINE_IMAGERY_KEY)
        if resolved is not None:
            return cast(EarthEngineImageryService, resolved)
    return get_default_imagery_engine()
