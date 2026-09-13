"""Repo-Triad Forge Service protocol, typed models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class RepoInspectionData(BaseModel):
    """Repository structural inspection and 5D complexity metrics."""

    repo_path: str = Field(..., description="Path to inspected repository")
    repo_name: str = Field(..., description="Repository folder name")
    languages: list[str] = Field(default_factory=list, description="Detected programming languages")
    packages: list[str] = Field(default_factory=list, description="Monorepo subpackages")
    has_git: bool = Field(default=True, description="Whether git repository is initialized")
    compute_tier: str = Field(default="High", description="Calibrated compute tier (High/Medium/Low)")
    composite_complexity: float = Field(default=0.8, description="5D composite complexity score 0.0-1.0")
    total_files: int = Field(default=0, description="Total source files discovered")
    blast_radius_roots: list[str] = Field(default_factory=list, description="Core architectural blast-radius files")


class KiCandidateData(BaseModel):
    """Candidate Knowledge Item with isnad citation lineage."""

    id: str = Field(..., description="Unique KI identifier")
    title: str = Field(..., description="Epistemic breakthrough title")
    domain: str = Field(default="software_engineering", description="Bounded ecosystem domain")
    claims_count: int = Field(default=2, description="Number of verifiable isnad claims")
    citations: list[str] = Field(default_factory=list, description="Source file and line citations")
    confidence: float = Field(default=0.9, description="Confidence score 0.0-1.0")


class TriadBriefData(BaseModel):
    """Scaffolded interactive HTML visual brief metadata."""

    slug: str = Field(..., description="Brief identifier slug")
    title: str = Field(..., description="Brief display title")
    html_path: str = Field(..., description="Absolute path to generated HTML file in %TEMP%")


class TriadPlanData(BaseModel):
    """Synthesized 5-stage triad pipeline implementation plan."""

    plan_markdown: str = Field(..., description="Detailed markdown implementation plan")
    stages_count: int = Field(default=5, description="Number of operational stages")
    estimated_duration_seconds: int = Field(default=300, description="Estimated execution budget")


class TriadRunData(BaseModel):
    """Result report of triad pipeline execution."""

    success: bool = Field(..., description="Whether pipeline completed successfully")
    stages_completed: list[str] = Field(default_factory=list, description="Stages executed")
    artifacts_generated: list[str] = Field(default_factory=list, description="Output artifacts")
    kis_committed: list[str] = Field(default_factory=list, description="Committed KI IDs in vault")
    message: str = Field(default="", description="Summary execution status message")


@runtime_checkable
class RepoTriadForgeService(Protocol):
    """Authoritative service protocol for the repository triad pipeline."""

    def inspect(self, repo_path: str) -> RepoInspectionData:
        """Inspect repository structure, language manifests, and evaluate 5D compute complexity."""
        ...

    def generate_briefs(
        self, repo_path: str, output_dir: str | None = None
    ) -> list[TriadBriefData]:
        """Generate 5 interactive dark-mode HTML visual briefs with Mermaid diagrams in %TEMP%."""
        ...

    def extract_kis(self, repo_path: str) -> list[KiCandidateData]:
        """Extract candidate Knowledge Items with isnad citations from repository."""
        ...

    def commit_kis(
        self, kis_data: list[dict[str, Any]], vault_dir: str | None = None
    ) -> list[str]:
        """Commit approved Knowledge Items as canonical dual-file directories (Rule 40)."""
        ...

    def run_pipeline(
        self, repo_path: str, options: dict[str, Any] | None = None
    ) -> TriadRunData:
        """Execute full 5-stage triad pipeline with bounded in-flight self-repair (Rule 25, 49)."""
        ...


REPO_TRIAD_FORGE_SERVICE_KEY: ServiceKey[RepoTriadForgeService] = ServiceKey(
    "service.repo_triad_forge"
)
