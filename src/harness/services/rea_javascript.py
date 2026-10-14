"""REA JavaScript & Web Forensics Service Protocol, models, and ServiceKey.

Elevates JavaScript source recovery (Wakaru ^1.13.0), Electron ASAR inspection,
passive CDP observation, .NET managed assembly inspection, and offline HAR capture
analysis into an IoC micro-kernel service seam.
Synthesized from REA (morluto/rea) JavaScript, browser, and dotnet modules.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceContext, ServiceKey


# -----------------------------------------------------------------------------
# Typed Domain Models & Response Envelopes
# -----------------------------------------------------------------------------


class ReaReportBase(BaseModel):
    """Base model with dictionary-style backward compatibility."""

    def __getitem__(self, key: str) -> Any:
        try:
            val = getattr(self, key)
            return val
        except AttributeError as err:
            raise KeyError(key) from err

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


class RecoveredSourceModule(ReaReportBase):
    """Recovered source file descriptor."""

    relative_path: str
    size_bytes: int = 0
    recovered_type: str = "javascript"


class RecoverSourcesReport(ReaReportBase):
    """Result envelope for Wakaru bundle deobfuscation and source recovery."""

    status: str = "ok"
    bundle_path: str
    output_dir: str
    wakaru_version: str = "1.14.0"
    modules_count: int = 0
    modules: list[RecoveredSourceModule] = Field(default_factory=list)
    sourcemap_applied: bool = False
    error: str | None = None


class ElectronIpcChannel(ReaReportBase):
    """Electron IPC channel descriptor."""

    channel_name: str
    direction: str = "bidirectional"  # main-to-renderer, renderer-to-main, bidirectional
    source_file: str = ""


class ElectronInspectReport(ReaReportBase):
    """Result envelope for Electron ASAR archive inspection."""

    status: str = "ok"
    asar_path: str
    app_name: str = ""
    app_version: str = ""
    main_script: str = ""
    preload_scripts: list[str] = Field(default_factory=list)
    ipc_channels: list[ElectronIpcChannel] = Field(default_factory=list)
    files_count: int = 0
    error: str | None = None


class WebObservationReport(ReaReportBase):
    """Result envelope for passive CDP observation."""

    status: str = "ok"
    cdp_endpoint: str
    target_id: str | None = None
    duration_ms: int = 10000
    dom_nodes_count: int = 0
    scripts_loaded: list[str] = Field(default_factory=list)
    listeners_count: int = 0
    network_requests_count: int = 0
    error: str | None = None


class DotnetTypeInfo(ReaReportBase):
    """Managed type information in a .NET assembly."""

    type_name: str
    namespace: str
    methods_count: int = 0
    cil_instruction_hash: str = ""


class DotnetInspectReport(ReaReportBase):
    """Result envelope for .NET managed PE/CLI assembly inspection."""

    status: str = "ok"
    assembly_path: str
    module_name: str = ""
    target_framework: str = ""
    types: list[DotnetTypeInfo] = Field(default_factory=list)
    pinvoke_imports: list[dict[str, str]] = Field(default_factory=list)
    native_boundaries: list[str] = Field(default_factory=list)
    error: str | None = None


class HarEntrySummary(ReaReportBase):
    """Summary of a single HAR request/response transaction."""

    method: str
    url: str
    status: int
    mime_type: str = ""
    response_size: int = 0


class HarInspectReport(ReaReportBase):
    """Result envelope for offline HAR capture analysis."""

    status: str = "ok"
    har_path: str
    entries_count: int = 0
    filtered_entries_count: int = 0
    entries: list[HarEntrySummary] = Field(default_factory=list)
    error: str | None = None


# -----------------------------------------------------------------------------
# Micro-Kernel IoC Service Protocol & Key
# -----------------------------------------------------------------------------


@runtime_checkable
class ReaJavaScriptService(Protocol):
    """Protocol for JavaScript, Web, Electron, and .NET analysis operations."""

    def recover_sources(
        self,
        bundle_path: str,
        output_dir: str,
        sourcemap_path: str | None = None,
    ) -> RecoverSourcesReport | dict[str, Any]:
        """Recover module directory trees and source maps via Wakaru ^1.13.0."""
        ...

    def electron_inspect(
        self,
        asar_path: str,
        extract_ipc: bool = True,
    ) -> ElectronInspectReport | dict[str, Any]:
        """Inspect Electron ASAR archives: manifest, processes, and IPC channels."""
        ...

    def web_observe(
        self,
        cdp_endpoint: str,
        target_id: str | None = None,
        duration_ms: int = 10000,
    ) -> WebObservationReport | dict[str, Any]:
        """Passive CDP observation of page DOM, scripts, event listeners, and network."""
        ...

    def dotnet_inspect(
        self,
        assembly_path: str,
        include_cil: bool = True,
    ) -> DotnetInspectReport | dict[str, Any]:
        """Open a managed .NET PE/CLI image: types, CIL hashes, and P/Invoke declarations."""
        ...

    def har_inspect(
        self,
        har_path: str,
        filter_status: int | None = None,
    ) -> HarInspectReport | dict[str, Any]:
        """Inspect offline HAR 1.2 or native mitmproxy capture records without network calls."""
        ...


REA_JAVASCRIPT_KEY: ServiceKey[ReaJavaScriptService] = ServiceKey("service.rea_javascript")


def resolve_rea_javascript(ctx: ServiceContext) -> ReaJavaScriptService | None:
    """Resolve ReaJavaScriptService from context if registered."""
    return ctx.optional(REA_JAVASCRIPT_KEY)
