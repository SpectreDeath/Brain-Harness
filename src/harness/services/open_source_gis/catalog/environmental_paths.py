"""Deterministic routing paths for environmental, terrain, LiDAR, and remote sensing workloads."""

from __future__ import annotations

from harness.services.open_source_gis.models import (
    EngineSelectionResult,
    GISEngineRecord,
    GISEngineScore,
    SpatialWorkloadProfile,
)


def try_environmental_routes(
    engines: dict[str, GISEngineRecord],
    profile: SpatialWorkloadProfile,
) -> EngineSelectionResult | None:
    """Attempt deterministic routing for environmental, LiDAR, DEM, and remote sensing workloads."""
    formats_upper = {fmt.upper() for fmt in profile.data_formats}
    domain_lower = profile.domain.lower()
    analysis_lower = profile.analysis.lower()

    # Path 1: LiDAR / Point Cloud
    if (
        profile.has_lidar
        or "LAS" in formats_upper
        or "LAZ" in formats_upper
        or domain_lower == "lidar_hydrology"
        or profile.geometry_type == "point_cloud"
    ):
        p_rec = engines.get("Whitebox GAT")
        s_rec = engines.get("SAGA GIS")
        primary_score = GISEngineScore(
            engine=p_rec,  # type: ignore
            fitness_score=0.96,
            matched_domains=("lidar_hydrology",),
            matched_formats=tuple(fmt for fmt in profile.data_formats if fmt.upper() in ("LAS", "LAZ")),
        )
        sec_score = (
            GISEngineScore(
                engine=s_rec,  # type: ignore
                fitness_score=0.82,
                matched_domains=("terrain_morphometry",),
                matched_formats=("GeoTIFF",),
            )
            if s_rec
            else None
        )
        return EngineSelectionResult(
            primary=primary_score,
            secondary=sec_score,
            composite_score=0.96,
            routing_path="lidar_hydrology_whitebox_gat",
            rationale="Whitebox GAT is the definitive open-source LiDAR and hydro-geomorphic DEM suite (successor to TAS, 410+ tools, LAS-to-shapefile).",
        )

    # Path 2: Terrain Morphometry / DEM derivatives (TWI / TPC)
    if (
        domain_lower in ("terrain_morphometry", "dem_derivatives")
        or "twi" in domain_lower
        or "twi" in analysis_lower
        or "morphometry" in analysis_lower
    ):
        p_rec = engines.get("SAGA GIS")
        s_rec = engines.get("GRASS GIS")
        primary_score = GISEngineScore(
            engine=p_rec,  # type: ignore
            fitness_score=0.94,
            matched_domains=("terrain_morphometry", "dem_derivatives"),
            matched_formats=("GeoTIFF",),
        )
        sec_score = (
            GISEngineScore(
                engine=s_rec,  # type: ignore
                fitness_score=0.85,
                matched_domains=("terrain_manipulation",),
                matched_formats=("GeoTIFF",),
            )
            if s_rec
            else None
        )
        return EngineSelectionResult(
            primary=primary_score,
            secondary=sec_score,
            composite_score=0.94,
            routing_path="terrain_morphometry_saga_gis",
            rationale="SAGA GIS provides industry-standard Topographic Wetness Index (TWI) and Topographic Position Classification for raster DEM morphometry.",
        )

    # Path 4: Remote Sensing / Multispectral Classification
    if (
        domain_lower in ("remote_sensing", "image_processing", "spectral_classification")
        or "spectral" in analysis_lower
    ):
        p_rec = engines.get("GRASS GIS")
        s_rec = engines.get("ILWIS")
        primary_score = GISEngineScore(
            engine=p_rec,  # type: ignore
            fitness_score=0.93,
            matched_domains=("remote_sensing", "image_processing"),
            matched_formats=("GeoTIFF",),
        )
        sec_score = (
            GISEngineScore(
                engine=s_rec,  # type: ignore
                fitness_score=0.80,
                matched_domains=("remote_sensing",),
                matched_formats=("GeoTIFF",),
            )
            if s_rec
            else None
        )
        return EngineSelectionResult(
            primary=primary_score,
            secondary=sec_score,
            composite_score=0.93,
            routing_path="remote_sensing_grass_gis",
            rationale="GRASS GIS brings 350+ validated tools trusted by NASA, NOAA, USDA, and USGS for rigorous satellite multispectral image processing.",
        )

    # Path 7: Watershed Delineation / EPA Basins
    if domain_lower in ("watershed_delineation", "epa_basins") or profile.sector == "epa_basins":
        p_rec = engines.get("MapWindow 5")
        s_rec = engines.get("Whitebox GAT")
        primary_score = GISEngineScore(
            engine=p_rec,  # type: ignore
            fitness_score=0.88,
            matched_domains=("watershed_delineation", "hydrology"),
            matched_formats=("Shapefile", "Basins_Formats"),
        )
        sec_score = (
            GISEngineScore(
                engine=s_rec,  # type: ignore
                fitness_score=0.84,
                matched_domains=("lidar_hydrology",),
                matched_formats=("GeoTIFF",),
            )
            if s_rec
            else None
        )
        return EngineSelectionResult(
            primary=primary_score,
            secondary=sec_score,
            composite_score=0.88,
            routing_path="watershed_delineation_mapwindow",
            rationale="MapWindow 5 directly integrates TauDEM for automated watershed delineation under the historical US EPA Basins project contract.",
        )

    # Path 12: Land & Water Management / Time Series
    if domain_lower in ("land_water_management", "time_series_raster") or profile.has_time_series:
        p_rec = engines.get("ILWIS")
        s_rec = engines.get("GRASS GIS")
        primary_score = GISEngineScore(
            engine=p_rec,  # type: ignore
            fitness_score=0.89,
            matched_domains=("land_water_management", "time_series_raster"),
            matched_formats=("GeoTIFF", "ILWIS_Raster"),
        )
        sec_score = (
            GISEngineScore(
                engine=s_rec,  # type: ignore
                fitness_score=0.82,
                matched_domains=("remote_sensing",),
                matched_formats=("GeoTIFF",),
            )
            if s_rec
            else None
        )
        return EngineSelectionResult(
            primary=primary_score,
            secondary=sec_score,
            composite_score=0.89,
            routing_path="land_water_management_ilwis",
            rationale="ILWIS is dedicated to integrated land and water resource modeling with advanced raster time-series playback and spectral analysis.",
        )

    return None
