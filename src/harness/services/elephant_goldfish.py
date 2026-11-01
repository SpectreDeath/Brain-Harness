"""Elephant-Goldfish Service protocol, models, and typed ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class SemanticBoundaryData(BaseModel):
    """Semantic altitude range data for a specification document."""

    feature_range_start: int = Field(default=1, description="Start line of FeatureRange")
    feature_range_end: int = Field(default=1, description="End line of FeatureRange")
    detailed_range_start: int = Field(default=1, description="Start line of DetailedRange")
    detailed_range_end: int = Field(default=1, description="End line of DetailedRange")
    total_lines: int = Field(default=0, description="Total document lines")
    has_boundaries: bool = Field(default=True, description="Whether explicit boundaries were detected")


class GoldfishFindingData(BaseModel):
    """Normalized finding emitted by a Goldfish reviewer persona."""

    id: str = Field(..., description="Unique finding identifier")
    severity: str = Field(default="Major", description="Finding severity (Blocker/Major/Nit)")
    reviewer_lens: str = Field(..., description="Reviewer persona lens identifier")
    line_start: int = Field(default=1, description="Starting line reference")
    line_end: int = Field(default=1, description="Ending line reference")
    description: str = Field(..., description="Detailed description of the finding")
    recommendation: str = Field(..., description="Actionable recommendation or fix")


class GoldfishReviewReportData(BaseModel):
    """Consolidated Goldfish review deliverable data."""

    target_file: str = Field(..., description="Path to reviewed specification file")
    stage: str = Field(default="all", description="Review stage name or preset")
    findings: list[GoldfishFindingData] = Field(default_factory=list, description="List of findings")
    completed_reviewers: list[str] = Field(default_factory=list, description="Reviewers that completed successfully")
    failed_reviewers: list[str] = Field(default_factory=list, description="Reviewers that timed out or failed")
    blocker_count: int = Field(default=0, description="Count of Blocker findings")
    major_count: int = Field(default=0, description="Count of Major findings")
    nit_count: int = Field(default=0, description="Count of Nit findings")


class DriftDivergenceData(BaseModel):
    """Specific divergence item between living specification and codebase."""

    category: str = Field(..., description="Divergence category (Missing Feature, Incomplete Model, etc.)")
    symbol_name: str = Field(..., description="Name of the affected symbol or entity")
    expected_behavior: str = Field(..., description="Behavior or presence declared in spec")
    observed_reality: str = Field(..., description="Actual codebase state observed")
    file_path: str = Field(default="", description="Relevant file path if located")


class DriftReportData(BaseModel):
    """Codebase drift assessment report data."""

    spec_path: str = Field(..., description="Specification file identifier or path")
    source_root: str = Field(..., description="Source code root scanned")
    divergences: list[DriftDivergenceData] = Field(default_factory=list, description="Identified divergences")
    has_drift: bool = Field(default=False, description="Whether any drift was detected")
    scanned_files_count: int = Field(default=0, description="Count of code files scanned")


@runtime_checkable
class ElephantGoldfishService(Protocol):
    """Authoritative service protocol for Elephant-Goldfish Model governance."""

    def extract_boundaries(self, content: str) -> SemanticBoundaryData:
        """Extract line ranges for FeatureRange and DetailedRange from spec markdown."""
        ...

    def review_spec(
        self, target_file: str, stage: str = "all"
    ) -> GoldfishReviewReportData:
        """Execute Goldfish review on target specification and return consolidated report."""
        ...

    def detect_drift(
        self, spec_content: str, source_root: str
    ) -> DriftReportData:
        """Analyze living spec content against codebase to detect implementation drift."""
        ...


ELEPHANT_GOLDFISH_SERVICE_KEY = ServiceKey[ElephantGoldfishService](
    "service.elephant_goldfish"
)

