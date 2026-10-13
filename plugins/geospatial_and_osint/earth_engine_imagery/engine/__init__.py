"""Earth Engine imagery engine subpackage facade."""

from __future__ import annotations

from plugins.geospatial_and_osint.earth_engine_imagery.engine.core import BaseEarthEngine
from plugins.geospatial_and_osint.earth_engine_imagery.engine.models import (
    CompositeResult,
    ImageDescription,
    SceneMetadata,
    SpectralIndexResult,
    ThumbnailResult,
)
from plugins.geospatial_and_osint.earth_engine_imagery.engine.protocols import (
    EARTH_ENGINE_IMAGERY_KEY,
    EarthEngineImageryService,
)
from plugins.geospatial_and_osint.earth_engine_imagery.engine.resolvers import (
    get_default_imagery_engine,
    resolve_earth_engine_imagery,
)
from plugins.geospatial_and_osint.earth_engine_imagery.engine.search import ImageSearchMixin
from plugins.geospatial_and_osint.earth_engine_imagery.engine.service import EarthEngineImageryEngine
from plugins.geospatial_and_osint.earth_engine_imagery.engine.spectral import SpectralProcessingMixin
from plugins.geospatial_and_osint.earth_engine_imagery.engine.temporal import TemporalCompositingMixin

__all__ = [
    "BaseEarthEngine",
    "CompositeResult",
    "EARTH_ENGINE_IMAGERY_KEY",
    "EarthEngineImageryEngine",
    "EarthEngineImageryService",
    "ImageDescription",
    "ImageSearchMixin",
    "SceneMetadata",
    "SpectralIndexResult",
    "SpectralProcessingMixin",
    "TemporalCompositingMixin",
    "ThumbnailResult",
    "get_default_imagery_engine",
    "resolve_earth_engine_imagery",
]
