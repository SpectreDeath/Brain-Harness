"""Deterministic routing paths for spatial statistics, survey, and biodiversity workloads."""

from __future__ import annotations

from harness.services.open_source_gis.models import (
    EngineSelectionResult,
    GISEngineRecord,
    GISEngineScore,
    SpatialWorkloadProfile,
)


def try_statistical_routes(
    engines: dict[str, GISEngineRecord],
    profile: SpatialWorkloadProfile,
) -> EngineSelectionResult | None:
    """Attempt deterministic routing for spatial statistics, survey, and biodiversity."""
    domain_lower = profile.domain.lower()
    analysis_lower = profile.analysis.lower()

    # Path 3: Spatial Statistics (Moran's I, LISA, spatial regression)
    if (
        profile.needs_statistics
        or domain_lower in ("spatial_statistics", "spatial_econometrics")
        or "moran" in analysis_lower
        or "regression" in analysis_lower
        or "lisa" in analysis_lower
    ):
        p_rec = engines.get("GeoDa")
        s_rec = engines.get("GRASS GIS")
        primary_score = GISEngineScore(
            engine=p_rec,  # type: ignore
            fitness_score=0.95,
            matched_domains=("spatial_statistics", "data_exploration"),
            matched_formats=("Shapefile", "GeoPackage"),
        )
        sec_score = (
            GISEngineScore(
                engine=s_rec,  # type: ignore
                fitness_score=0.78,
                matched_domains=("spatial_statistics",),
                matched_formats=("Shapefile",),
            )
            if s_rec
            else None
        )
        return EngineSelectionResult(
            primary=primary_score,
            secondary=sec_score,
            composite_score=0.95,
            routing_path="spatial_statistics_geoda",
            rationale="GeoDa is the premier academic and research environment for spatial data exploration, Moran's I, LISA clusters, and spatial regression.",
        )

    # Path 6: Field Survey / Mobile GPS
    if (
        profile.needs_mobile
        or domain_lower in ("field_survey", "mobile_gps")
        or profile.output_type == "mobile_gps"
    ):
        p_rec = engines.get("gvSIG")
        s_rec = engines.get("Birdi")
        primary_score = GISEngineScore(
            engine=p_rec,  # type: ignore
            fitness_score=0.90,
            matched_domains=("field_survey", "cad_gis"),
            matched_formats=("GeoPackage", "Shapefile"),
        )
        sec_score = (
            GISEngineScore(
                engine=s_rec,  # type: ignore
                fitness_score=0.74,
                matched_domains=("drone_inspections",),
                matched_formats=("GeoTIFF",),
                warnings=("Birdi operates on a freemium tier model",),
            )
            if s_rec
            else None
        )
        return EngineSelectionResult(
            primary=primary_score,
            secondary=sec_score,
            composite_score=0.90,
            routing_path="field_survey_gvsig_mobile",
            rationale="gvSIG Mobile provides dedicated GPS field survey integration coupled with desktop OpenCAD snapping and NavTable inspection.",
        )

    # Path 8: Biodiversity / Species Distribution
    if (
        domain_lower in ("biodiversity", "species_distribution")
        or "species" in analysis_lower
        or "dna" in analysis_lower
    ):
        p_rec = engines.get("Diva GIS")
        s_rec = engines.get("GeoDa")
        primary_score = GISEngineScore(
            engine=p_rec,  # type: ignore
            fitness_score=0.86,
            matched_domains=("biodiversity", "species_distribution"),
            matched_formats=("WorldClim_Grid", "Shapefile"),
        )
        sec_score = (
            GISEngineScore(
                engine=s_rec,  # type: ignore
                fitness_score=0.72,
                matched_domains=("spatial_statistics",),
                matched_formats=("Shapefile",),
            )
            if s_rec
            else None
        )
        return EngineSelectionResult(
            primary=primary_score,
            secondary=sec_score,
            composite_score=0.86,
            routing_path="biodiversity_diva_gis",
            rationale="Diva GIS is custom-built for biologists to model species richness and DNA marker distributions using WorldClim climate extractions.",
        )

    return None
