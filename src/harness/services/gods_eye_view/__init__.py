"""God's Eye View Planetary OSINT & Spatial Intelligence service package."""

from __future__ import annotations

from .keys import GODS_EYE_VIEW_SERVICE_KEY
from .models import (
    AircraftTrackRecord,
    AnalystQueryResult,
    CctvCameraRecord,
    CctvSnapshotResult,
    CycloneRecord,
    EarthquakeRecord,
    FlightRecord,
    ImageryRenderResult,
    InfrastructureRecord,
    MilitaryAwarenessSummary,
    MilitaryContact,
    SatellitePassRecord,
    SituationBriefResult,
    TerrainHeightRecord,
    ThermalHotspotRecord,
    VesselRecord,
    VesselTrackRecord,
    WeatherMapResult,
    WeatherResult,
)
from .protocols import GodsEyeViewService
from .resolvers import (
    GodsEyeViewAdapter,
    attach_provenance_envelope,
    resolve_gods_eye_view,
)

__all__ = [
    "AircraftTrackRecord",
    "AnalystQueryResult",
    "CctvCameraRecord",
    "CctvSnapshotResult",
    "CycloneRecord",
    "EarthquakeRecord",
    "FlightRecord",
    "GODS_EYE_VIEW_SERVICE_KEY",
    "GodsEyeViewAdapter",
    "GodsEyeViewService",
    "ImageryRenderResult",
    "InfrastructureRecord",
    "MilitaryAwarenessSummary",
    "MilitaryContact",
    "SatellitePassRecord",
    "SituationBriefResult",
    "TerrainHeightRecord",
    "ThermalHotspotRecord",
    "VesselRecord",
    "VesselTrackRecord",
    "WeatherMapResult",
    "WeatherResult",
    "attach_provenance_envelope",
    "resolve_gods_eye_view",
]
