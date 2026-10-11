"""Deterministic routing paths for acoustics, OGC web services, vector conflation, and cartography."""

from __future__ import annotations

from harness.services.open_source_gis.models import (
    EngineSelectionResult,
    GISEngineRecord,
    GISEngineScore,
    SpatialWorkloadProfile,
)


def try_vector_web_routes(
    engines: dict[str, GISEngineRecord],
    profile: SpatialWorkloadProfile,
) -> EngineSelectionResult | None:
    """Attempt deterministic routing for acoustics, OGC web services, conflation, or fallback cartography."""
    formats_upper = {fmt.upper() for fmt in profile.data_formats}
    domain_lower = profile.domain.lower()
    analysis_lower = profile.analysis.lower()

    # Path 9: Urban Acoustics / Noise Mapping
    if domain_lower in ("urban_acoustics", "noise_mapping") or "noise" in analysis_lower:
        p_rec = engines.get("OrbisGIS")
        s_rec = engines.get("QGIS 3")
        primary_score = GISEngineScore(
            engine=p_rec,  # type: ignore
            fitness_score=0.82,
            matched_domains=("urban_acoustics", "noise_mapping"),
            matched_formats=("GeoJSON", "Shapefile"),
            warnings=("OrbisGIS is an academic research package with evolving documentation",),
        )
        sec_score = (
            GISEngineScore(
                engine=s_rec,  # type: ignore
                fitness_score=0.80,
                matched_domains=("cartography",),
                matched_formats=("GeoPackage",),
            )
            if s_rec
            else None
        )
        return EngineSelectionResult(
            primary=primary_score,
            secondary=sec_score,
            composite_score=0.82,
            routing_path="urban_acoustics_orbisgis",
            rationale="OrbisGIS provides built-in urban acoustic and noise mapping algorithms powered by research-grade H2GIS spatial SQL.",
        )

    # Path 10: OGC Web Services
    if (
        domain_lower in ("ogc_web_services", "wms_wfs")
        or "WMS" in formats_upper
        or "WFS" in formats_upper
        or "WPS" in formats_upper
    ):
        p_rec = engines.get("uDig")
        s_rec = engines.get("OpenJUMP")
        primary_score = GISEngineScore(
            engine=p_rec,  # type: ignore
            fitness_score=0.85,
            matched_domains=("ogc_web_services", "basic_mapping"),
            matched_formats=("WMS", "WFS"),
        )
        sec_score = (
            GISEngineScore(
                engine=s_rec,  # type: ignore
                fitness_score=0.76,
                matched_domains=("vector_conflation",),
                matched_formats=("Shapefile",),
            )
            if s_rec
            else None
        )
        return EngineSelectionResult(
            primary=primary_score,
            secondary=sec_score,
            composite_score=0.85,
            routing_path="ogc_services_udig",
            rationale="uDig is an Internet-oriented GIS built specifically to consume OGC standard web services (WMS, WFS, WPS) with Mapnik integration.",
        )

    # Path 11: Vector Conflation / Large Datasets
    if domain_lower in ("vector_conflation", "large_vector_overlay") or "conflation" in analysis_lower:
        p_rec = engines.get("OpenJUMP")
        s_rec = engines.get("QGIS 3")
        primary_score = GISEngineScore(
            engine=p_rec,  # type: ignore
            fitness_score=0.87,
            matched_domains=("vector_conflation", "large_vector_overlay"),
            matched_formats=("Shapefile", "GeoJSON"),
        )
        sec_score = (
            GISEngineScore(
                engine=s_rec,  # type: ignore
                fitness_score=0.85,
                matched_domains=("cartography",),
                matched_formats=("GeoPackage",),
            )
            if s_rec
            else None
        )
        return EngineSelectionResult(
            primary=primary_score,
            secondary=sec_score,
            composite_score=0.87,
            routing_path="vector_conflation_openjump",
            rationale="OpenJUMP (JAVA Unified Mapping Platform) excels at vector geometry conflation and high-throughput rendering of heavy vector layers.",
        )

    # Fallback: General Cartography -> QGIS 3
    p_rec = engines.get("QGIS 3")
    s_rec = engines.get("GRASS GIS")
    primary_score = GISEngineScore(
        engine=p_rec,  # type: ignore
        fitness_score=0.98,
        matched_domains=("cartography", "3d_visualization", "general_gis"),
        matched_formats=("GeoPackage", "Shapefile", "GeoTIFF"),
    )
    sec_score = (
        GISEngineScore(
            engine=s_rec,  # type: ignore
            fitness_score=0.88,
            matched_domains=("terrain_manipulation",),
            matched_formats=("GeoTIFF",),
        )
        if s_rec
        else None
    )
    return EngineSelectionResult(
        primary=primary_score,
        secondary=sec_score,
        composite_score=0.98,
        routing_path="cartography_qgis3",
        rationale="QGIS 3 is the flagship open-source GIS offering complete ArcGIS Pro parity, 3D cartography, and an unmatched PyQGIS ecosystem.",
    )
