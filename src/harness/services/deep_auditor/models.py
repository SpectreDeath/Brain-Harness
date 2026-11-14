"""Slotted and frozen domain models for the Deep Repo Auditor service (Rules 12, 43)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class ComputeDimensionVector:
    """5-dimensional complexity profile and model budget recommendation."""

    ambiguity: float
    span: float
    depth: float
    rigor: float
    concurrency: float
    composite: float
    tier: str
    thinking_budget: str

    def __post_init__(self) -> None:
        dims = {
            "ambiguity": self.ambiguity,
            "span": self.span,
            "depth": self.depth,
            "rigor": self.rigor,
            "concurrency": self.concurrency,
            "composite": self.composite,
        }
        for label, val in dims.items():
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{label} must be within [0.0, 1.0], got {val!r}")
        if not self.tier.strip():
            raise ValueError("tier must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "ambiguity": self.ambiguity,
            "span": self.span,
            "depth": self.depth,
            "rigor": self.rigor,
            "concurrency": self.concurrency,
            "composite": self.composite,
            "tier": self.tier,
            "thinking_budget": self.thinking_budget,
        }


@dataclass(slots=True, frozen=True)
class AxisFinding:
    """Single introspection axis outcome with source evidence and remediation items."""

    axis: str
    title: str
    status: str
    summary: str
    evidence: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.axis.strip() or not self.title.strip():
            raise ValueError("AxisFinding requires non-empty axis and title")

    def to_dict(self) -> dict[str, Any]:
        return {
            "axis": self.axis,
            "title": self.title,
            "status": self.status,
            "summary": self.summary,
            "evidence": list(self.evidence),
            "recommendations": list(self.recommendations),
        }


@dataclass(slots=True, frozen=True)
class TopologyNodeSummary:
    """Structural topology classification and bounded codebase surface metrics."""

    topology_pattern: str
    root_manifest: str
    nesting_depth: int
    total_files_scanned: int
    python_files: int
    plugin_count: int
    skill_count: int
    test_file_count: int
    has_git: bool
    blast_radius_modules: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "nesting_depth",
            "total_files_scanned",
            "python_files",
            "plugin_count",
            "skill_count",
            "test_file_count",
        ):
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "topology_pattern": self.topology_pattern,
            "root_manifest": self.root_manifest,
            "nesting_depth": self.nesting_depth,
            "total_files_scanned": self.total_files_scanned,
            "python_files": self.python_files,
            "plugin_count": self.plugin_count,
            "skill_count": self.skill_count,
            "test_file_count": self.test_file_count,
            "has_git": self.has_git,
            "blast_radius_modules": list(self.blast_radius_modules),
        }


@dataclass(slots=True, frozen=True)
class VisualBriefPaths:
    """File paths to the three generated HTML visual briefs."""

    compute_brief: str
    topology_brief: str
    repo_reader_brief: str
    output_dir: str

    def __post_init__(self) -> None:
        if not all((self.compute_brief, self.topology_brief, self.repo_reader_brief, self.output_dir)):
            raise ValueError("VisualBriefPaths requires all brief and directory paths")

    def to_dict(self) -> dict[str, Any]:
        return {
            "compute_brief": self.compute_brief,
            "topology_brief": self.topology_brief,
            "repo_reader_brief": self.repo_reader_brief,
            "output_dir": self.output_dir,
        }


@dataclass(slots=True, frozen=True)
class DeepAuditReport:
    """Complete 4-axis audit report with compute and topology assessments."""

    repo_root: str
    resolved_root: str
    timestamp_iso: str
    compute: ComputeDimensionVector
    topology: TopologyNodeSummary
    axes: tuple[AxisFinding, ...]

    def __post_init__(self) -> None:
        if len(self.axes) != 4:
            raise ValueError(f"DeepAuditReport must include exactly 4 axes, got {len(self.axes)}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "resolved_root": self.resolved_root,
            "timestamp_iso": self.timestamp_iso,
            "compute": self.compute.to_dict(),
            "topology": self.topology.to_dict(),
            "axes": [axis.to_dict() for axis in self.axes],
        }


__all__ = [
    "AxisFinding",
    "ComputeDimensionVector",
    "DeepAuditReport",
    "TopologyNodeSummary",
    "VisualBriefPaths",
]
