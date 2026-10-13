"""EarthEngineImageryEngine composite service class unifying sub-mixins."""

from __future__ import annotations

from plugins.geospatial_and_osint.earth_engine_imagery.engine.search import ImageSearchMixin
from plugins.geospatial_and_osint.earth_engine_imagery.engine.spectral import SpectralProcessingMixin
from plugins.geospatial_and_osint.earth_engine_imagery.engine.temporal import TemporalCompositingMixin


class EarthEngineImageryEngine(
    ImageSearchMixin,
    SpectralProcessingMixin,
    TemporalCompositingMixin,
):
    """Core satellite imagery and spectral computation engine."""

    def __init__(self) -> None:
        super().__init__()
