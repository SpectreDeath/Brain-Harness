"""R Runtime and Language Server Service Protocol, Models, and ServiceKey."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceContext, ServiceKey


class RDiagnosticItemData(BaseModel):
    """Pydantic representation of an R Language Server diagnostic item."""

    file_path: str = Field(..., description="Target file path or URI of diagnostic")
    line: int = Field(default=0, description="0-indexed line number")
    column: int = Field(default=0, description="0-indexed character column offset")
    severity: str = Field(default="Warning", description="Diagnostic severity: Error, Warning, Information, Hint")
    message: str = Field(..., description="Diagnostic textual explanation")
    code: str | None = Field(default=None, description="Diagnostic lint or parser rule code")


class RSessionInspectionData(BaseModel):
    """Pydantic representation of an R runtime session inspection report."""

    pid: int = Field(..., description="R process ID")
    working_dir: str = Field(..., description="Working directory of R process")
    loaded_packages: list[str] = Field(default_factory=list, description="List of loaded package namespaces")
    global_symbols: list[str] = Field(default_factory=list, description="Variables and symbols in .GlobalEnv")
    active_device: str = Field(default="jgd", description="Active graphics device (e.g. jgd, png, null)")
    is_clean: bool = Field(default=True, description="True if no internal symbols leaked into user space")


class RPlotEventData(BaseModel):
    """Pydantic representation of an R graphics device event packet."""

    plot_index: int = Field(default=0, description="Sequence index of the generated plot")
    width: float = Field(default=800.0, description="Plot width in pixels / points")
    height: float = Field(default=600.0, description="Plot height in pixels / points")
    format: str = Field(default="json", description="Plot encoding format (json, svg, png)")
    payload_size: int = Field(default=0, description="Payload byte length")
    timestamp: float = Field(default=0.0, description="Generation epoch timestamp")


class RLanguageServerConfigData(BaseModel):
    """Pydantic configuration parameters for R Language Server."""

    r_path: str = Field(..., description="Executable path to R binary")
    server_args: list[str] = Field(default_factory=list, description="Arguments passed to R language server")
    debounce_ms: int = Field(default=300, description="Debounce delay in ms before triggering AST lint")
    lint_on_change: bool = Field(default=True, description="Whether to compute diagnostics on didChange")
    max_payload_mb: int = Field(default=10, description="Maximum allowed payload size in MB")


@runtime_checkable
class RRuntimeProtocol(Protocol):
    """Service protocol for R runtime operations, LSP interaction, and graphics streaming."""

    def inspect_session(
        self,
        pid: int,
        working_dir: str,
        loaded_packages: list[str] | None = None,
        global_symbols: list[str] | None = None,
        active_device: str = "jgd",
    ) -> RSessionInspectionData:
        """Inspect active R process session state, namespaces, and device status."""
        ...

    def parse_diagnostics(
        self, raw_diagnostics: list[dict[str, Any]]
    ) -> list[RDiagnosticItemData]:
        """Parse raw LSP or lintr diagnostic dictionaries into normalized items."""
        ...

    def stream_plot(
        self,
        plot_index: int,
        width: float,
        height: float,
        format: str = "json",
        payload_size: int = 1024,
    ) -> RPlotEventData:
        """Process and serialize an R graphics device display-list packet."""
        ...

    def validate_config(
        self,
        config: RLanguageServerConfigData,
    ) -> bool:
        """Validate R Language Server configuration parameters against safety boundaries."""
        ...


R_RUNTIME_SERVICE_KEY: ServiceKey[RRuntimeProtocol] = ServiceKey("service.r_runtime")


def resolve_r_runtime(context: ServiceContext) -> RRuntimeProtocol:
    """Resolve RRuntimeProtocol service from the IoC container."""
    return context.require(R_RUNTIME_SERVICE_KEY)

