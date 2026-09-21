"""Gemini & Vercel Streaming Chatbot service protocol, typed models, and ServiceKey.

Elevates the Gemini & Vercel plain-text chunk streaming, CORS preflight gate,
and client stream reader engine into a first-class micro-kernel IoC service seam.
Synthesized from Johnson Samuel's literature (freeCodeCamp, 2026, ki_20260918_gemini_vercel_streaming).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class AuditCheckData(BaseModel):
    """Data transfer model for an individual diagnostic check."""

    rule_id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human-readable rule name")
    passed: bool = Field(..., description="Whether the check passed")
    message: str = Field(..., description="Diagnostic message or violation details")
    severity: str = Field(default="error", description="Severity level: error, warning, info")
    line_number: int | None = Field(default=None, description="Source code line number if applicable")


class AuditReportData(BaseModel):
    """Data transfer model for full diagnostic evaluation results."""

    target: str = Field(..., description="Target file path or label")
    passed: bool = Field(..., description="Whether all error-level checks passed")
    checks: list[AuditCheckData] = Field(default_factory=list, description="Executed checks")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Execution metrics")


class ScaffoldConfigData(BaseModel):
    """Data transfer model for application scaffolding configuration."""

    app_name: str = Field(..., description="Application name identifier")
    framework: str = Field(default="react", description="Frontend framework: react, solid, vanilla")
    language: str = Field(default="javascript", description="Language: javascript, typescript")
    model: str = Field(default="gemini-2.5-flash", description="Gemini model identifier")
    max_text_length: int = Field(default=2000, description="Max input character length")
    max_array_length: int = Field(default=50, description="Max payload array cardinality")
    allowed_origin: str = Field(default="https://yourdomain.com", description="CORS allowed origin")
    output_dir: str = Field(default=".", description="Destination directory path")


class ScaffoldResultData(BaseModel):
    """Data transfer model for application scaffolding output."""

    files: dict[str, str] = Field(default_factory=dict, description="Generated filename to content mapping")
    manifest: dict[str, Any] = Field(default_factory=dict, description="Scaffolding metadata manifest")


class StreamSimulationData(BaseModel):
    """Data transfer model for stream simulation output."""

    prompt: str = Field(..., description="Original prompt text")
    chunks: list[str] = Field(default_factory=list, description="Simulated plain-text chunks")
    reconstructed_text: str = Field(..., description="Reconstructed text from chunks")
    total_chunks: int = Field(..., description="Total chunk count")
    duration_ms: float = Field(..., description="Simulated generation time in ms")


@runtime_checkable
class GeminiVercelStreamingService(Protocol):
    """Protocol for Gemini & Vercel streaming static analysis, scaffolding, and verification."""

    def audit_code(self, source_code: str, file_path: str = "") -> AuditReportData:
        """Run static analysis against the 5 production streaming rubrics."""
        ...

    def scaffold_app(self, config: ScaffoldConfigData) -> ScaffoldResultData:
        """Generate a production 3-tier Gemini & Vercel streaming application."""
        ...

    def simulate_stream(self, prompt: str, chunks_count: int = 5) -> StreamSimulationData:
        """Simulate unbuffered plain-text chunk streaming."""
        ...

    def generate_visual_brief(self, output_path: str | Path | None = None) -> Path:
        """Generate interactive HTML Visual Brief with telemetry and topology diagram."""
        ...


GEMINI_VERCEL_STREAMING_SERVICE_KEY: ServiceKey[GeminiVercelStreamingService] = ServiceKey(
    "service.gemini_vercel_streaming"
)
