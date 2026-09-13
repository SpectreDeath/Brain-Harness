"""PR Lens Visualizer Service protocol, data models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class PrLensValidationData(BaseModel):
    """Validation report for a graph document."""

    valid: bool = Field(..., description="Whether the graph document is valid")
    issues: list[dict[str, Any]] = Field(
        default_factory=list, description="List of validation errors and warnings"
    )
    errors_count: int = Field(default=0, description="Count of blocking errors")
    warnings_count: int = Field(default=0, description="Count of non-blocking warnings")


class PrLensRenderData(BaseModel):
    """Rendered standalone SVG diagram result."""

    svg_content: str = Field(..., description="Standalone zero-dependency animated SVG XML string")
    node_count: int = Field(default=0, description="Number of rendered nodes")
    edge_count: int = Field(default=0, description="Number of rendered edges")
    lane_count: int = Field(default=0, description="Number of architectural lanes")
    theme: str = Field(default="auto", description="Active color theme mode")


class PrLensDiffData(BaseModel):
    """Git diff extraction result."""

    diff_text: str = Field(..., description="Extracted unified diff text")
    files_changed: list[str] = Field(
        default_factory=list, description="List of modified, added, or deleted file paths"
    )
    stats: dict[str, int] = Field(
        default_factory=dict, description="Diff change statistics (insertions, deletions)"
    )


class PrLensAnalysisData(BaseModel):
    """Analysis result mapping git diff into graph document and walkthrough."""

    summary: str = Field(..., description="Architectural summary of changes")
    graph_doc: dict[str, Any] = Field(
        ..., description="Assembled GraphDocument dictionary structure"
    )
    walkthrough: list[dict[str, Any]] = Field(
        default_factory=list, description="Ordered progressive disclosure walkthrough steps"
    )


class PrLensCommentData(BaseModel):
    """Formatted GitHub PR markdown comment payload."""

    markdown_comment: str = Field(
        ..., description="Markdown comment ready for posting to GitHub PR"
    )
    has_diagram: bool = Field(default=True, description="Whether diagram is embedded")
    has_walkthrough: bool = Field(default=True, description="Whether walkthrough is included")


@runtime_checkable
class PrLensGraphService(Protocol):
    """Service protocol for PR Lens graph validation, rendering, diffing, and commenting."""

    def validate(self, graph_doc: dict[str, Any]) -> PrLensValidationData:
        """Validate structural and semantic integrity of a graph document."""
        ...

    def render(
        self,
        graph_doc: dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> PrLensRenderData:
        """Render a graph document into a standalone animated SVG."""
        ...

    def diff(
        self,
        base_ref: str = "HEAD~1",
        head_ref: str = "HEAD",
        repo_path: str | None = None,
    ) -> PrLensDiffData:
        """Extract unified git diff between two commit references."""
        ...

    def analyze(
        self,
        diff_text: str,
        overlay_map: dict[str, Any] | None = None,
    ) -> PrLensAnalysisData:
        """Analyze diff text and synthesize a GraphDocument with optional architectural overlay."""
        ...

    def comment(
        self,
        analysis: dict[str, Any],
        svg_content: str,
    ) -> PrLensCommentData:
        """Compose GitHub PR markdown comment enclosing diagram and progressive walkthrough."""
        ...


PR_LENS_GRAPH_SERVICE_KEY: ServiceKey[PrLensGraphService] = ServiceKey(
    "service.pr_lens_graph"
)
