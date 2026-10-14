"""Engine subpackage for REA JavaScript & Web Forensics.

Unifies Wakaru recovery, Electron ASAR inspection, passive CDP observation,
.NET PE inspection, and offline HAR capture analysis into an authoritative facade.
"""

from __future__ import annotations

from typing import Any

from .dotnet import DotnetInspector
from .electron import ElectronInspector
from .har import HarInspector
from .models import DotnetTypeInfo, HarEntryInfo, IpcChannelInfo, PinvokeImportInfo, RecoveredChunk
from .resolvers import resolve_rea_javascript_engine
from .wakaru import WakaruRecoverer
from .web_cdp import WebCdpObserver


class ReaJavaScriptEngine:
    """Composite domain engine delegating to partitioned modality analyzers."""

    def __init__(self, wakaru_path: str | None = None) -> None:
        self.wakaru = WakaruRecoverer(wakaru_path=wakaru_path)
        self.electron = ElectronInspector()
        self.web_cdp = WebCdpObserver()
        self.dotnet = DotnetInspector()
        self.har = HarInspector()

    def recover_sources(
        self,
        bundle_path: str,
        output_dir: str,
        sourcemap_path: str | None = None,
    ) -> dict[str, Any]:
        """Recover module directory trees and source maps via Wakaru ^1.13.0."""
        return self.wakaru.recover(bundle_path=bundle_path, output_dir=output_dir, sourcemap_path=sourcemap_path)

    def electron_inspect(
        self,
        asar_path: str,
        extract_ipc: bool = True,
    ) -> dict[str, Any]:
        """Inspect Electron ASAR archive for packages, entry scripts, and IPC channels."""
        return self.electron.inspect(asar_path=asar_path, extract_ipc=extract_ipc)

    def web_observe(
        self,
        cdp_endpoint: str,
        target_id: str | None = None,
        duration_ms: int = 10000,
    ) -> dict[str, Any]:
        """Passive Chrome DevTools Protocol observation of DOM and loaded scripts."""
        return self.web_cdp.observe(cdp_endpoint=cdp_endpoint, target_id=target_id, duration_ms=duration_ms)

    def dotnet_inspect(
        self,
        assembly_path: str,
        include_cil: bool = True,
    ) -> dict[str, Any]:
        """Open managed .NET PE/CLI image: inventory types, CIL hashes, and P/Invoke calls."""
        return self.dotnet.inspect(assembly_path=assembly_path, include_cil=include_cil)

    def har_inspect(
        self,
        har_path: str,
        filter_status: int | None = None,
    ) -> dict[str, Any]:
        """Inspect offline HAR 1.2 or native mitmproxy capture records."""
        return self.har.inspect(har_path=har_path, filter_status=filter_status)


__all__ = [
    "DotnetInspector",
    "DotnetTypeInfo",
    "ElectronInspector",
    "HarEntryInfo",
    "HarInspector",
    "IpcChannelInfo",
    "PinvokeImportInfo",
    "ReaJavaScriptEngine",
    "RecoveredChunk",
    "WakaruRecoverer",
    "WebCdpObserver",
    "resolve_rea_javascript_engine",
]
