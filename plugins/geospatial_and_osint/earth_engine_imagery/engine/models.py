"""Slotted domain models for Earth Engine satellite imagery and spectral computations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SceneMetadata:
    """Metadata describing a candidate satellite scene."""

    id: str
    date: str
    cloud_cover_percentage: float
    crs: str
    bands: list[str] = field(default_factory=list)
    resolution_meters: float = 10.0


@dataclass(slots=True)
class SpectralIndexResult:
    """Result of a spectral index computation (NDVI, NDWI, EVI, NBR, or CUSTOM)."""

    status: str
    mode: str
    image_id: str
    index_type: str
    formula: str
    output_band: str
    valid_range: list[float] = field(default_factory=lambda: [-1.0, 1.0])
    typical_vegetation_threshold: float = 0.4
    description: str = ""


@dataclass(slots=True)
class CompositeResult:
    """Result of multi-temporal composite reductions."""

    status: str
    mode: str
    collection_id: str
    bbox: list[float]
    temporal_window: list[str]
    composite_method: str
    mask_clouds_applied: bool = True
    estimated_source_scenes: int = 18
    retained_clear_pixels_percentage: float = 94.2
    output_asset_type: str = "Image"


@dataclass(slots=True)
class ThumbnailResult:
    """Metadata and URL for a visual thumbnail preview."""

    status: str
    mode: str
    image_id: str
    thumbnail_url: str
    vis_params: dict[str, Any] = field(default_factory=dict)
    dimensions: str = "512x512"
    format: str = "PNG"


@dataclass(slots=True)
class ImageDescription:
    """Structural properties and band definitions for a satellite image asset."""

    status: str
    mode: str
    image_id: str
    type: str = "Image"
    bands_count: int = 12
    bands: list[str] = field(default_factory=list)
    spatial_resolution_meters: float = 10.0
    crs: str = "EPSG:32610"
    sensor: str = "MSI"
    spacecraft: str = "Sentinel-2B"
    radiometric_resolution_bits: int = 12
