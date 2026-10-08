"""Domain models and exceptions for Open-Source GIS Architecture.

Enforces:
- Rule 12: Slotted & frozen dataclasses (slots=True, frozen=True)
- Rule 43: Direct attribute mutation assertion invariants
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


# ---------------------------------------------------------------------------
# Domain Exceptions
# ---------------------------------------------------------------------------


class FalconViewRestrictedDomainError(ValueError):
    """Raised when a workload targets the defense-restricted FalconView domain in a civilian context."""


class CRSProjectionError(ValueError):
    """Raised when metric spatial calculations are attempted on unprojected geographic coordinate systems."""


class TopologyValidationError(ValueError):
    """Raised when spatial geometries fail topological integrity rules."""


# ---------------------------------------------------------------------------
# Slotted & Frozen Domain Models (Rule 12 & Rule 43)
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class SpatialWorkloadProfile:
    """Classified spatial workload features guiding engine selection."""

    geometry_type: str
    domain: str
    data_formats: tuple[str, ...] = ()
    sector: str = "civilian"
    output_type: str = "analytical_report"
    scale_gb: float = 0.0
    has_lidar: bool = False
    has_time_series: bool = False
    needs_mobile: bool = False
    needs_statistics: bool = False
    analysis: str = ""

    def __post_init__(self) -> None:
        if self.sector == "defense_restricted":
            raise FalconViewRestrictedDomainError(
                "Sector 'defense_restricted' halted under safety boundary. "
                "FalconView cannot be deployed in civilian spatial pipelines."
            )


@dataclass(slots=True, frozen=True)
class GISEngineRecord:
    """Authoritative benchmark record for an open-source GIS engine."""

    name: str
    star_rating: float
    license: str
    maturity: str
    sector_flags: tuple[str, ...]
    primary_domains: tuple[str, ...]
    specialized_tools: tuple[str, ...]
    python_api: str | None
    supported_formats: tuple[str, ...]
    negative_boundary: str
    arcgis_parity: bool
    article_note: str

    def __post_init__(self) -> None:
        assert 0.0 <= self.star_rating <= 5.0, f"Star rating {self.star_rating} out of [0.0, 5.0] bounds"


@dataclass(slots=True, frozen=True)
class GISEngineScore:
    """Calculated fitness score of an engine for a specific workload."""

    engine: GISEngineRecord
    fitness_score: float
    matched_domains: tuple[str, ...]
    matched_formats: tuple[str, ...]
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        assert 0.0 <= self.fitness_score <= 1.0, f"Fitness score {self.fitness_score} out of [0.0, 1.0] bounds"


@dataclass(slots=True, frozen=True)
class EngineSelectionResult:
    """Primary and secondary recommended GIS engines with routing rationale."""

    primary: GISEngineScore
    secondary: GISEngineScore | None
    composite_score: float
    routing_path: str
    rationale: str

    def __post_init__(self) -> None:
        assert self.composite_score >= 0.0, f"Composite score {self.composite_score} cannot be negative"


@dataclass(slots=True, frozen=True)
class SpatialPipelineStep:
    """Single node in a spatial execution DAG with CRS safety verification."""

    step_id: int
    operation: str
    engine: str
    input_crs: str
    output_crs: str
    input_format: str
    output_format: str

    METRIC_OPERATIONS: ClassVar[tuple[str, ...]] = (
        "buffer",
        "area",
        "distance",
        "density",
        "watershed_delineation",
        "slope_aspect",
    )

    def __post_init__(self) -> None:
        if (
            self.operation.lower() in self.METRIC_OPERATIONS
            and self.input_crs.upper() in ("EPSG:4326", "WGS84", "CRS84")
        ):
            raise CRSProjectionError(
                f"Step {self.step_id} ({self.operation}) cannot execute on unprojected geographic CRS ({self.input_crs}). "
                "Reproject to conformal planar/metric CRS (e.g. UTM) before executing metric spatial operations."
            )


@dataclass(slots=True, frozen=True)
class SpatialPipelineDAG:
    """Directed acyclic graph of spatial pipeline steps."""

    steps: tuple[SpatialPipelineStep, ...]
    total_steps: int

    def __post_init__(self) -> None:
        assert self.total_steps == len(self.steps), f"Step count mismatch: {self.total_steps} vs {len(self.steps)}"


@dataclass(slots=True, frozen=True)
class TopologyAuditReport:
    """Structural report on geometric errors and sliver polygons."""

    is_valid: bool
    sliver_count: int
    self_intersection_count: int
    unclosed_rings: int
    duplicate_vertices: int
    repair_actions: tuple[str, ...] = ()
    severity: str = "OK"

    def __post_init__(self) -> None:
        assert self.severity in ("OK", "WARNING", "CRITICAL"), f"Invalid severity: {self.severity}"
        if not self.is_valid and self.severity == "OK":
            raise ValueError("Invalid topology cannot have severity OK")


@dataclass(slots=True, frozen=True)
class GisVisualBriefResult:
    """Result receipt from generating an interactive HTML visual brief."""

    report_path: str
    report_url: str
    rendered_nodes: int
    timestamp: str


@dataclass(slots=True, frozen=True)
class SpatialArchitectureReceipt:
    """Authoritative receipt summarizing full spatial architecture interrogation."""

    primary_engine: str
    primary_fitness: float
    routing_path: str
    secondary_engine: str | None
    pipeline_valid: bool
    pipeline_step_count: int
    topology_severity: str
    visual_brief_path: str | None
    receipt_markdown: str


__all__ = [
    "CRSProjectionError",
    "EngineSelectionResult",
    "FalconViewRestrictedDomainError",
    "GISEngineRecord",
    "GISEngineScore",
    "GisVisualBriefResult",
    "SpatialArchitectureReceipt",
    "SpatialPipelineDAG",
    "SpatialPipelineStep",
    "SpatialWorkloadProfile",
    "TopologyAuditReport",
    "TopologyValidationError",
]
