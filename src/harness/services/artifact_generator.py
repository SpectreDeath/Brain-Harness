"""Artifact and Report Generator Service protocol, models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class MermaidResult(BaseModel):
    """Result of Mermaid diagram synthesis."""

    status: str = Field(default="ok", description="Status indicator")
    mermaid: str = Field(default="", description="Generated valid Mermaid diagram syntax")
    nodes_count: int = Field(default=0, description="Count of rendered nodes")
    edges_count: int = Field(default=0, description="Count of rendered edges")
    error: str | None = Field(default=None, description="Error details if synthesis failed")


class HtmlReportResult(BaseModel):
    """Result of HTML report generation."""

    status: str = Field(default="ok", description="Status indicator")
    title: str = Field(default="", description="Report title")
    sections_count: int = Field(default=0, description="Count of rendered sections")
    output_path: str | None = Field(default=None, description="Path where HTML was written, if provided")
    html_length: int = Field(default=0, description="Total byte/character length of full HTML")
    error: str | None = Field(default=None, description="Error details if generation failed")


class BriefingResult(BaseModel):
    """Result of structured executive briefing creation."""

    status: str = Field(default="ok", description="Status indicator")
    title: str = Field(default="", description="Briefing title")
    markdown: str = Field(default="", description="Generated Markdown document content")
    output_path: str | None = Field(default=None, description="Path where file was written, if provided")
    error: str | None = Field(default=None, description="Error details if creation failed")


@runtime_checkable
class ArtifactGeneratorService(Protocol):
    """Protocol for generating Mermaid diagrams, responsive HTML reports, and executive briefings."""

    def generate_mermaid(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        direction: str = "TD",
    ) -> MermaidResult:
        """Synthesize valid Mermaid flowchart syntax."""
        ...

    def generate_html_report(
        self,
        title: str,
        sections: list[dict[str, Any]],
        output_path: str | None = None,
        theme: str = "dark",
    ) -> HtmlReportResult:
        """Generate a responsive, standalone HTML report."""
        ...

    def create_briefing(
        self,
        title: str,
        summary: str,
        metrics: dict[str, Any] | None = None,
        recommendations: list[str] | None = None,
        output_path: str | None = None,
    ) -> BriefingResult:
        """Create a structured executive briefing document."""
        ...


ARTIFACT_GENERATOR_KEY: ServiceKey[ArtifactGeneratorService] = ServiceKey("service.artifact_generator")
