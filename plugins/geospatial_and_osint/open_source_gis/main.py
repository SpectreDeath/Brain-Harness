"""Open-Source GIS Architect Plugin & HarnessPlugin Service Implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.open_source_gis import (
    OPEN_SOURCE_GIS_SERVICE_KEY,
    DefaultOpenSourceGisService,
    EngineSelectionResult,
    GisVisualBriefResult,
    OpenSourceGisService,
    SpatialArchitectureReceipt,
    SpatialPipelineDAG,
    SpatialWorkloadProfile,
    TopologyAuditReport,
)

logger = structlog.get_logger(__name__)

# Global engine instance for standalone tool execution and service provision
_SERVICE_INSTANCE = DefaultOpenSourceGisService()


def _get_service() -> DefaultOpenSourceGisService:
    return _SERVICE_INSTANCE


# ---------------------------------------------------------------------------
# Standalone Tool Entrypoints (for Agent Tool Invocation)
# ---------------------------------------------------------------------------


def gis_route_workload(
    domain: str,
    geometry_type: str = "vector_polygon",
    data_formats: list[str] | None = None,
    sector: str = "civilian",
    analysis: str = "",
    has_lidar: bool = False,
    needs_statistics: bool = False,
    needs_mobile: bool = False,
) -> dict[str, Any]:
    """Route spatial analysis workloads to optimal open-source GIS engines using deterministic fitness matching."""
    service = _get_service()
    profile = SpatialWorkloadProfile(
        geometry_type=geometry_type,
        domain=domain,
        data_formats=tuple(data_formats or []),
        sector=sector,
        analysis=analysis,
        has_lidar=has_lidar,
        needs_statistics=needs_statistics,
        needs_mobile=needs_mobile,
    )
    result = service.route_workload(profile)

    return {
        "routing_path": result.routing_path,
        "composite_score": result.composite_score,
        "primary_engine": {
            "name": result.primary.engine.name,
            "star_rating": result.primary.engine.star_rating,
            "fitness_score": result.primary.fitness_score,
            "license": result.primary.engine.license,
            "python_api": result.primary.engine.python_api,
            "matched_domains": list(result.primary.matched_domains),
            "matched_formats": list(result.primary.matched_formats),
            "warnings": list(result.primary.warnings),
        },
        "secondary_engine": (
            {
                "name": result.secondary.engine.name,
                "star_rating": result.secondary.engine.star_rating,
                "fitness_score": result.secondary.fitness_score,
                "license": result.secondary.engine.license,
                "python_api": result.secondary.engine.python_api,
                "matched_domains": list(result.secondary.matched_domains),
                "matched_formats": list(result.secondary.matched_formats),
                "warnings": list(result.secondary.warnings),
            }
            if result.secondary
            else None
        ),
        "rationale": result.rationale,
    }


def gis_validate_pipeline(steps: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate spatial pipeline steps for CRS planar projection safety and format handoffs."""
    service = _get_service()
    valid, messages, dag = service.validate_pipeline_dag(steps)
    return {
        "is_valid": valid,
        "messages": messages,
        "total_steps": dag.total_steps if dag else 0,
    }


def gis_audit_topology(
    features: list[dict[str, Any]], sliver_threshold_m2: float = 0.05
) -> dict[str, Any]:
    """Audit vector polygon geometries for topological errors (self-intersections, unclosed rings, slivers)."""
    service = _get_service()
    report = service.audit_topology(features, sliver_threshold_m2=sliver_threshold_m2)
    return {
        "is_valid": report.is_valid,
        "severity": report.severity,
        "sliver_count": report.sliver_count,
        "self_intersection_count": report.self_intersection_count,
        "unclosed_rings": report.unclosed_rings,
        "duplicate_vertices": report.duplicate_vertices,
        "repair_actions": list(report.repair_actions),
    }


def gis_architect_workload(
    workload_profile: dict[str, Any],
    pipeline_steps: list[dict[str, Any]] | None = None,
    features: list[dict[str, Any]] | None = None,
    generate_brief: bool = True,
) -> dict[str, Any]:
    """End-to-end composite spatial workload architecture interrogation."""
    service = _get_service()
    receipt = service.architect_workload(
        profile_data=workload_profile,
        pipeline_steps=pipeline_steps,
        features=features,
        generate_brief=generate_brief,
    )
    return {
        "primary_engine": receipt.primary_engine,
        "primary_fitness": receipt.primary_fitness,
        "routing_path": receipt.routing_path,
        "secondary_engine": receipt.secondary_engine,
        "pipeline_valid": receipt.pipeline_valid,
        "pipeline_step_count": receipt.pipeline_step_count,
        "topology_severity": receipt.topology_severity,
        "visual_brief_path": receipt.visual_brief_path,
        "receipt_markdown": receipt.receipt_markdown,
    }


# ---------------------------------------------------------------------------
# Harness Plugin Class & Singleton (Rule 45)
# ---------------------------------------------------------------------------


class OpenSourceGisPlugin(HarnessPlugin, OpenSourceGisService):
    """Brain Harness plugin exposing open-source GIS engine selection, CRS validation & topology auditing."""

    name = "plugin.open_source_gis"
    version = "1.0.0"
    description = (
        "Open-source GIS analytical engine selector, CRS projection safety validator, "
        "topology hygiene auditor, and visual brief generator across 14 GIS engines."
    )
    trusted = True

    def __init__(self) -> None:
        super().__init__()
        self._service = _SERVICE_INSTANCE

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [OPEN_SOURCE_GIS_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(OPEN_SOURCE_GIS_SERVICE_KEY, self)
        logger.info("open_source_gis_plugin_loaded")

    async def on_enable(self) -> None:
        logger.info("open_source_gis_plugin_enabled")

    async def on_disable(self) -> None:
        logger.info("open_source_gis_plugin_disabled")

    async def on_unload(self) -> None:
        logger.info("open_source_gis_plugin_unloaded")

    # Delegate OpenSourceGisService Protocol methods
    def route_workload(
        self, profile: SpatialWorkloadProfile, weights: dict[str, float] | None = None
    ) -> EngineSelectionResult:
        return self._service.route_workload(profile, weights=weights)

    def validate_pipeline_dag(
        self, steps: list[dict[str, Any]]
    ) -> tuple[bool, list[str], SpatialPipelineDAG | None]:
        return self._service.validate_pipeline_dag(steps)

    def audit_topology(
        self, features: list[dict[str, Any]], sliver_threshold_m2: float = 0.05
    ) -> TopologyAuditReport:
        return self._service.audit_topology(features, sliver_threshold_m2=sliver_threshold_m2)

    def generate_visual_brief(
        self,
        profile: SpatialWorkloadProfile,
        selection: EngineSelectionResult,
        dag: SpatialPipelineDAG | None = None,
        topology: TopologyAuditReport | None = None,
        output_path: str | Path | None = None,
    ) -> GisVisualBriefResult:
        return self._service.generate_visual_brief(
            profile=profile,
            selection=selection,
            dag=dag,
            topology=topology,
            output_path=output_path,
        )

    def architect_workload(
        self,
        profile_data: dict[str, Any],
        pipeline_steps: list[dict[str, Any]] | None = None,
        features: list[dict[str, Any]] | None = None,
        generate_brief: bool = True,
    ) -> SpatialArchitectureReceipt:
        return self._service.architect_workload(
            profile_data=profile_data,
            pipeline_steps=pipeline_steps,
            features=features,
            generate_brief=generate_brief,
        )


# Explicit module-level singleton (Rule 45)
plugin = OpenSourceGisPlugin()
