"""Service protocol, default implementation, and single-seam resolver for Open-Source GIS."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.open_source_gis.catalog import GISEngineCatalog
from harness.services.open_source_gis.models import (
    EngineSelectionResult,
    GisVisualBriefResult,
    SpatialArchitectureReceipt,
    SpatialPipelineDAG,
    SpatialWorkloadProfile,
    TopologyAuditReport,
)
from harness.services.open_source_gis.validator import (
    audit_topology as validate_topology_func,
    validate_pipeline_dag as validate_dag_func,
)
from harness.services.open_source_gis.visualizer import generate_visual_brief as generate_brief_func


# ---------------------------------------------------------------------------
# Service Protocol & Key (Rule 49 & Rule 2)
# ---------------------------------------------------------------------------


@runtime_checkable
class OpenSourceGisService(Protocol):
    """Protocol for open-source GIS engine selection, pipeline validation, and topology auditing."""

    def route_workload(
        self, profile: SpatialWorkloadProfile, weights: dict[str, float] | None = None
    ) -> EngineSelectionResult:
        """Route workload to optimal primary and secondary open-source GIS engines."""
        ...

    def validate_pipeline_dag(
        self, steps: list[dict[str, Any]]
    ) -> tuple[bool, list[str], SpatialPipelineDAG | None]:
        """Validate pipeline steps for CRS projection safety and build SpatialPipelineDAG."""
        ...

    def audit_topology(
        self, features: list[dict[str, Any]], sliver_threshold_m2: float = 0.05
    ) -> TopologyAuditReport:
        """Audit geometry rings for self-intersections, unclosed rings, and slivers."""
        ...

    def generate_visual_brief(
        self,
        profile: SpatialWorkloadProfile,
        selection: EngineSelectionResult,
        dag: SpatialPipelineDAG | None = None,
        topology: TopologyAuditReport | None = None,
        output_path: str | Path | None = None,
    ) -> GisVisualBriefResult:
        """Generate an interactive dark-theme HTML visual brief with Mermaid DAG."""
        ...

    def architect_workload(
        self,
        profile_data: dict[str, Any],
        pipeline_steps: list[dict[str, Any]] | None = None,
        features: list[dict[str, Any]] | None = None,
        generate_brief: bool = True,
    ) -> SpatialArchitectureReceipt:
        """Execute end-to-end workload architecture interrogation, routing, and receipt generation."""
        ...


OPEN_SOURCE_GIS_SERVICE_KEY: ServiceKey[OpenSourceGisService] = ServiceKey(
    "open_source_gis_service"
)


# ---------------------------------------------------------------------------
# Default Service Implementation
# ---------------------------------------------------------------------------


class DefaultOpenSourceGisService:
    """Production implementation of OpenSourceGisService."""

    def __init__(self, catalog: GISEngineCatalog | None = None) -> None:
        self.catalog = catalog or GISEngineCatalog()

    def route_workload(
        self, profile: SpatialWorkloadProfile, weights: dict[str, float] | None = None
    ) -> EngineSelectionResult:
        """Route workload using deterministic engine catalog."""
        return self.catalog.route_workload(profile, weights=weights)

    def validate_pipeline_dag(
        self, steps: list[dict[str, Any]]
    ) -> tuple[bool, list[str], SpatialPipelineDAG | None]:
        """Validate pipeline steps for CRS projection safety and build SpatialPipelineDAG."""
        return validate_dag_func(steps)

    def audit_topology(
        self, features: list[dict[str, Any]], sliver_threshold_m2: float = 0.05
    ) -> TopologyAuditReport:
        """Audit geometry rings for basic topological defects."""
        return validate_topology_func(features, sliver_threshold_m2=sliver_threshold_m2)

    def generate_visual_brief(
        self,
        profile: SpatialWorkloadProfile,
        selection: EngineSelectionResult,
        dag: SpatialPipelineDAG | None = None,
        topology: TopologyAuditReport | None = None,
        output_path: str | Path | None = None,
    ) -> GisVisualBriefResult:
        """Generate self-contained dark-theme HTML visual brief complying with Rule 51."""
        return generate_brief_func(
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
        """End-to-end composite execution of GIS workload interrogation."""
        profile = SpatialWorkloadProfile(
            geometry_type=profile_data.get("geometry_type") or "vector_polygon",
            domain=profile_data.get("domain") or "general_gis",
            data_formats=tuple(profile_data.get("data_formats") or []),
            sector=profile_data.get("sector") or "civilian",
            output_type=profile_data.get("output_type") or "analytical_report",
            scale_gb=float(profile_data.get("scale_gb") or 0.0),
            has_lidar=bool(profile_data.get("has_lidar", False)),
            has_time_series=bool(profile_data.get("has_time_series", False)),
            needs_mobile=bool(profile_data.get("needs_mobile", False)),
            needs_statistics=bool(profile_data.get("needs_statistics", False)),
            analysis=profile_data.get("analysis") or "",
        )

        selection = self.route_workload(profile)

        dag: SpatialPipelineDAG | None = None
        dag_valid = True
        dag_count = 0
        if pipeline_steps:
            dag_valid, _, dag = self.validate_pipeline_dag(pipeline_steps)
            if dag:
                dag_count = dag.total_steps

        topo_report: TopologyAuditReport | None = None
        topo_severity = "OK"
        if features:
            topo_report = self.audit_topology(features)
            topo_severity = topo_report.severity

        brief_res: GisVisualBriefResult | None = None
        if generate_brief:
            brief_res = self.generate_visual_brief(
                profile=profile,
                selection=selection,
                dag=dag,
                topology=topo_report,
            )

        md_receipt = (
            f"### [Spatial Architecture Receipt]\n"
            f"- **Primary Engine**: `{selection.primary.engine.name}` (Fitness: {selection.primary.fitness_score:.2f})\n"
            f"- **Routing Path**: `{selection.routing_path}`\n"
            f"- **Secondary Engine**: `{selection.secondary.engine.name if selection.secondary else 'None'}`\n"
            f"- **Pipeline Valid**: `{dag_valid}` ({dag_count} steps)\n"
            f"- **Topology Health**: `{topo_severity}`\n"
        )
        if brief_res:
            md_receipt += f"- **Visual Brief**: [{Path(brief_res.report_path).name}]({brief_res.report_url})\n"

        return SpatialArchitectureReceipt(
            primary_engine=selection.primary.engine.name,
            primary_fitness=selection.primary.fitness_score,
            routing_path=selection.routing_path,
            secondary_engine=selection.secondary.engine.name if selection.secondary else None,
            pipeline_valid=dag_valid,
            pipeline_step_count=dag_count,
            topology_severity=topo_severity,
            visual_brief_path=brief_res.report_path if brief_res else None,
            receipt_markdown=md_receipt,
        )


def resolve_open_source_gis(
    ctx: ServiceContext | None = None,
) -> OpenSourceGisService:
    """Resolve OpenSourceGisService from IoC context or fall back to DefaultOpenSourceGisService (Rule 58)."""
    if ctx is not None:
        svc = ctx.optional(OPEN_SOURCE_GIS_SERVICE_KEY)
        if svc is not None and isinstance(svc, OpenSourceGisService):
            return svc
    return DefaultOpenSourceGisService()


__all__ = [
    "DefaultOpenSourceGisService",
    "OPEN_SOURCE_GIS_SERVICE_KEY",
    "OpenSourceGisService",
    "resolve_open_source_gis",
]
