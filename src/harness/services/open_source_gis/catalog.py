"""Authoritative catalog and deterministic router for 14 open-source GIS engines."""

from __future__ import annotations

import json
from pathlib import Path

import structlog
import yaml

from harness.services.open_source_gis.models import (
    EngineSelectionResult,
    GISEngineRecord,
    GISEngineScore,
    SpatialWorkloadProfile,
)

logger = structlog.get_logger(__name__)


class GISEngineCatalog:
    """Authoritative catalog and deterministic router for 14 open-source GIS engines."""

    def __init__(self, engines: list[GISEngineRecord] | None = None) -> None:
        if engines is None:
            self.engines = self._load_default_catalog()
        else:
            self.engines = engines
        self._by_name = {e.name: e for e in self.engines}
        self._default_weights = self._load_default_weights()

    @classmethod
    def _find_resource_file(cls, filename: str) -> Path | None:
        """Locate catalog or config file across workspace roots."""
        current = Path(__file__).resolve()
        workspace_root: Path | None = None
        for p in current.parents:
            if (p / "pyproject.toml").exists() or (p / ".git").exists():
                workspace_root = p
                break
        if workspace_root is None:
            workspace_root = current.parents[4]

        candidates = [
            workspace_root
            / ".agents"
            / "skills"
            / "open-source-gis-architect"
            / "resources"
            / filename,
            workspace_root
            / "plugins"
            / "geospatial_and_osint"
            / "open_source_gis"
            / filename,
            workspace_root
            / ".agents"
            / "skills"
            / "open-source-gis-architect"
            / filename,
        ]
        for p in candidates:
            if p.exists():
                return p
        return None

    @classmethod
    def _load_default_catalog(cls) -> list[GISEngineRecord]:
        matrix_path = cls._find_resource_file("gis_engine_matrix.json")
        if not matrix_path or not matrix_path.exists():
            return cls._fallback_engine_catalog()

        try:
            data = json.loads(matrix_path.read_text(encoding="utf-8"))
            records: list[GISEngineRecord] = []
            for item in data:
                records.append(
                    GISEngineRecord(
                        name=item["name"],
                        star_rating=float(item["star_rating"]),
                        license=item["license"],
                        maturity=item["maturity"],
                        sector_flags=tuple(item.get("sector_flags") or []),
                        primary_domains=tuple(item.get("primary_domains") or []),
                        specialized_tools=tuple(item.get("specialized_tools") or []),
                        python_api=item.get("python_api"),
                        supported_formats=tuple(item.get("supported_formats") or []),
                        negative_boundary=item.get("negative_boundary", ""),
                        arcgis_parity=bool(item.get("arcgis_parity", False)),
                        article_note=item.get("article_note", ""),
                    )
                )
            return records
        except Exception as err:
            logger.warning("failed_loading_engine_matrix", error=str(err))
            return cls._fallback_engine_catalog()

    @classmethod
    def _load_default_weights(cls) -> dict[str, float]:
        cfg_path = cls._find_resource_file("config.default.yaml")
        if cfg_path and cfg_path.exists():
            try:
                cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
                if cfg and "scoring_weights" in cfg:
                    return {str(k): float(v) for k, v in cfg["scoring_weights"].items()}
            except Exception as err:
                logger.debug("config_load_weights_fallback", error=str(err))
        return {
            "analytical_depth": 0.35,
            "cartography": 0.20,
            "specialized_tooling": 0.25,
            "automation_scripting": 0.20,
        }

    @classmethod
    def _fallback_engine_catalog(cls) -> list[GISEngineRecord]:
        """Builtin fallback definitions for top GIS engines."""
        return [
            GISEngineRecord(
                name="QGIS 3",
                star_rating=5.0,
                license="GPL-2.0",
                maturity="production",
                sector_flags=("civilian", "academic", "environmental"),
                primary_domains=("cartography", "3d_visualization", "general_gis"),
                specialized_tools=("PyQGIS", "Processing Toolbox", "QGIS Server"),
                python_api="qgis.core",
                supported_formats=("GeoPackage", "Shapefile", "GeoTIFF", "PostGIS"),
                negative_boundary="Heavy point clouds without downsampling",
                arcgis_parity=True,
                article_note="The flagship open source GIS suite with complete commercial parity.",
            ),
            GISEngineRecord(
                name="SAGA GIS",
                star_rating=4.5,
                license="GPL-2.0",
                maturity="production",
                sector_flags=("academic", "environmental"),
                primary_domains=("terrain_morphometry", "dem_derivatives"),
                specialized_tools=("Topographic Wetness Index", "Landform Classification"),
                python_api="saga-gis-python",
                supported_formats=("GeoTIFF", "SAGA_Grid", "Shapefile"),
                negative_boundary="Print cartography and web services",
                arcgis_parity=False,
                article_note="Specialized geoscientific analysis system for DEM morphometry.",
            ),
            GISEngineRecord(
                name="Whitebox GAT",
                star_rating=4.5,
                license="GPL-3.0",
                maturity="production",
                sector_flags=("academic", "environmental"),
                primary_domains=("lidar_hydrology", "point_clouds"),
                specialized_tools=("LAS to DEM", "LiDAR Bare Earth Filtering", "Hydro Delineation"),
                python_api="whitebox",
                supported_formats=("LAS", "LAZ", "GeoTIFF", "Shapefile"),
                negative_boundary="Mobile capture or vector editing",
                arcgis_parity=False,
                article_note="Definitive open-source LiDAR and hydro-geomorphic DEM suite.",
            ),
            GISEngineRecord(
                name="GRASS GIS",
                star_rating=4.5,
                license="GPL-2.0",
                maturity="production",
                sector_flags=("civilian", "academic", "environmental", "governmental"),
                primary_domains=("remote_sensing", "image_processing"),
                specialized_tools=("i.cluster", "r.watershed", "350+ validated modules"),
                python_api="grass.script",
                supported_formats=("GeoTIFF", "Shapefile", "GRASS_Raster"),
                negative_boundary="Simple desktop ad-hoc viewing",
                arcgis_parity=True,
                article_note="NASA and NOAA trust standard for remote sensing and raster modeling.",
            ),
            GISEngineRecord(
                name="GeoDa",
                star_rating=4.0,
                license="GPL-3.0",
                maturity="production",
                sector_flags=("academic", "public_health", "economic"),
                primary_domains=("spatial_statistics", "spatial_econometrics"),
                specialized_tools=("Moran's I", "LISA Clusters", "Spatial Regression"),
                python_api="pygeoda",
                supported_formats=("Shapefile", "GeoPackage", "GeoJSON"),
                negative_boundary="Raster manipulation and remote sensing",
                arcgis_parity=False,
                article_note="Premier spatial data exploration and spatial econometrics package.",
            ),
            GISEngineRecord(
                name="gvSIG",
                star_rating=4.0,
                license="GPL-2.0",
                maturity="production",
                sector_flags=("civilian", "field_survey"),
                primary_domains=("field_survey", "cad_gis"),
                specialized_tools=("gvSIG Mobile", "OpenCAD Snapping", "NavTable"),
                python_api="jython_gvsig",
                supported_formats=("Shapefile", "GeoPackage", "DWG"),
                negative_boundary="LiDAR point clouds",
                arcgis_parity=False,
                article_note="Desktop GIS with mobile surveying and CAD precision tools.",
            ),
            GISEngineRecord(
                name="MapWindow 5",
                star_rating=3.5,
                license="MPL-1.1",
                maturity="production",
                sector_flags=("civilian", "environmental"),
                primary_domains=("watershed_delineation", "hydrology"),
                specialized_tools=("TauDEM Integration", "EPA Basins Modeler"),
                python_api=None,
                supported_formats=("Shapefile", "GeoTIFF"),
                negative_boundary="Linux server headless deployments",
                arcgis_parity=False,
                article_note="Extensible desktop GIS integrating TauDEM for watershed modeling.",
            ),
            GISEngineRecord(
                name="Diva GIS",
                star_rating=3.5,
                license="Free",
                maturity="maintenance",
                sector_flags=("academic", "biological"),
                primary_domains=("biodiversity", "species_distribution"),
                specialized_tools=("Species Richness", "WorldClim Climate Modeling"),
                python_api=None,
                supported_formats=("WorldClim_Grid", "Shapefile"),
                negative_boundary="Urban CAD snapping or metric topology",
                arcgis_parity=False,
                article_note="Tailored for biologists mapping species richness and climate envelopes.",
            ),
        ]

    def get_engine(self, name: str) -> GISEngineRecord | None:
        return self._by_name.get(name)

    def route_workload(
        self, profile: SpatialWorkloadProfile, weights: dict[str, float] | None = None
    ) -> EngineSelectionResult:
        """Route workload to optimal primary and secondary GIS engines using deterministic paths."""
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
            p_rec = self._by_name.get("Whitebox GAT")
            s_rec = self._by_name.get("SAGA GIS")
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
            p_rec = self._by_name.get("SAGA GIS")
            s_rec = self._by_name.get("GRASS GIS")
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

        # Path 3: Spatial Statistics (Moran's I, LISA, spatial regression)
        if (
            profile.needs_statistics
            or domain_lower in ("spatial_statistics", "spatial_econometrics")
            or "moran" in analysis_lower
            or "regression" in analysis_lower
            or "lisa" in analysis_lower
        ):
            p_rec = self._by_name.get("GeoDa")
            s_rec = self._by_name.get("GRASS GIS")
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

        # Path 4: Remote Sensing / Multispectral Classification
        if (
            domain_lower in ("remote_sensing", "image_processing", "spectral_classification")
            or "spectral" in analysis_lower
        ):
            p_rec = self._by_name.get("GRASS GIS")
            s_rec = self._by_name.get("ILWIS")
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

        # Path 6: Field Survey / Mobile GPS
        if (
            profile.needs_mobile
            or domain_lower in ("field_survey", "mobile_gps")
            or profile.output_type == "mobile_gps"
        ):
            p_rec = self._by_name.get("gvSIG")
            s_rec = self._by_name.get("Birdi")
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

        # Path 7: Watershed Delineation / EPA Basins
        if (
            domain_lower in ("watershed_delineation", "epa_basins")
            or profile.sector == "epa_basins"
        ):
            p_rec = self._by_name.get("MapWindow 5")
            s_rec = self._by_name.get("Whitebox GAT")
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

        # Path 8: Biodiversity / Species Distribution
        if (
            domain_lower in ("biodiversity", "species_distribution")
            or "species" in analysis_lower
            or "dna" in analysis_lower
        ):
            p_rec = self._by_name.get("Diva GIS")
            s_rec = self._by_name.get("GeoDa")
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

        # Path 9: Urban Acoustics / Noise Mapping
        if domain_lower in ("urban_acoustics", "noise_mapping") or "noise" in analysis_lower:
            p_rec = self._by_name.get("OrbisGIS")
            s_rec = self._by_name.get("QGIS 3")
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
            p_rec = self._by_name.get("uDig")
            s_rec = self._by_name.get("OpenJUMP")
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
            p_rec = self._by_name.get("OpenJUMP")
            s_rec = self._by_name.get("QGIS 3")
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

        # Path 12: Land & Water Management / Time Series
        if (
            domain_lower in ("land_water_management", "time_series_raster")
            or profile.has_time_series
        ):
            p_rec = self._by_name.get("ILWIS")
            s_rec = self._by_name.get("GRASS GIS")
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

        # Fallback: General Cartography -> QGIS 3
        p_rec = self._by_name.get("QGIS 3")
        s_rec = self._by_name.get("GRASS GIS")
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


__all__ = ["GISEngineCatalog"]
