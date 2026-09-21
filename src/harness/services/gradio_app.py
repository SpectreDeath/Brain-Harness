"""Gradio App Architect service protocol, typed models, and ServiceKey.

Elevates the Gradio App Architect production engineering, AST diagnostic inspection,
and scaffolding engine into a first-class micro-kernel IoC service seam.
Synthesized from Eva J Patel's literature (freeCodeCamp, 2026, ki-gradio-app-architect).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class DiagnosticCheckData(BaseModel):
    """Data transfer model for an individual diagnostic check."""

    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human-readable rule name")
    passed: bool = Field(..., description="Whether the check passed")
    message: str = Field(..., description="Diagnostic message or violation details")
    severity: str = Field(default="error", description="Severity level: error, warning, info")
    line_number: int | None = Field(default=None, description="Source code line number if applicable")


class DiagnosticReportData(BaseModel):
    """Data transfer model for full AST diagnostic evaluation results."""

    target: str = Field(..., description="Target file path or label")
    passed: bool = Field(..., description="Whether all error-level checks passed")
    checks: list[DiagnosticCheckData] = Field(default_factory=list, description="Executed checks")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Execution metrics")


class AppScaffoldConfigData(BaseModel):
    """Data transfer model for app scaffolding configuration."""

    app_name: str = Field(..., description="Application name identifier")
    topology: str = Field(default="blocks", description="Topology: blocks, chat, interface")
    enable_queue: bool = Field(default=True, description="Enable queued concurrency")
    concurrency_limit: int = Field(default=5, description="Concurrent execution bound")
    max_queue_size: int = Field(default=50, description="Maximum pending queue size")
    output_dir: str = Field(default=".", description="Destination directory path")


class AppScaffoldResultData(BaseModel):
    """Data transfer model for app scaffolding output."""

    files: dict[str, str] = Field(default_factory=dict, description="Generated filename to content mapping")
    manifest: dict[str, Any] = Field(default_factory=dict, description="Scaffolding metadata manifest")


@runtime_checkable
class GradioAppArchitectService(Protocol):
    """Protocol for Gradio application AST diagnostics, scaffolding, and brief generation."""

    def audit_code(self, source_code: str, file_path: str = "") -> DiagnosticReportData:
        """Run AST static analysis against the 5 production Gradio rubrics."""
        ...

    def scaffold_app(self, config: AppScaffoldConfigData) -> AppScaffoldResultData:
        """Generate a decoupled production Gradio application."""
        ...

    def generate_visual_brief(self, output_path: str | Path | None = None) -> Path:
        """Generate interactive HTML Visual Brief with telemetry and topology diagram."""
        ...


GRADIO_APP_ARCHITECT_SERVICE_KEY: ServiceKey[GradioAppArchitectService] = ServiceKey(
    "service.gradio_app_architect"
)
