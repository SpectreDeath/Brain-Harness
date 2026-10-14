"""REA JavaScript & Web Forensics Plugin for Brain Harness."""

from __future__ import annotations

from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.rea_javascript import (
    REA_JAVASCRIPT_KEY,
    ReaJavaScriptService,
)
from .engine import ReaJavaScriptEngine, resolve_rea_javascript_engine

logger = structlog.get_logger(__name__)

_GLOBAL_ENGINE = ReaJavaScriptEngine()


# -----------------------------------------------------------------------------
# Top-Level Entrypoint Tool Handlers Matching Manifest Signatures
# -----------------------------------------------------------------------------


def rea_javascript_recover_sources(
    bundle_path: str,
    output_dir: str,
    sourcemap_path: str | None = None,
) -> dict[str, Any]:
    """Recover module directory trees and source maps from minified/bundled scripts via Wakaru ^1.13.0."""
    return _GLOBAL_ENGINE.recover_sources(bundle_path=bundle_path, output_dir=output_dir, sourcemap_path=sourcemap_path)


def rea_javascript_electron_inspect(
    asar_path: str,
    extract_ipc: bool = True,
) -> dict[str, Any]:
    """Inspect Electron ASAR archives: manifest, processes, preload scripts, and declared IPC event channels."""
    return _GLOBAL_ENGINE.electron_inspect(asar_path=asar_path, extract_ipc=extract_ipc)


def rea_javascript_web_observe(
    cdp_endpoint: str,
    target_id: str | None = None,
    duration_ms: int = 10000,
) -> dict[str, Any]:
    """Passive Chrome DevTools Protocol observation of page DOM structure, loaded scripts, event listeners, and network activity."""
    return _GLOBAL_ENGINE.web_observe(cdp_endpoint=cdp_endpoint, target_id=target_id, duration_ms=duration_ms)


def rea_javascript_dotnet_inspect(
    assembly_path: str,
    include_cil: bool = True,
) -> dict[str, Any]:
    """Open a managed .NET PE/CLI image: inventory type hierarchies, CIL hashes, and P/Invoke declarations."""
    return _GLOBAL_ENGINE.dotnet_inspect(assembly_path=assembly_path, include_cil=include_cil)


def rea_javascript_har_inspect(
    har_path: str,
    filter_status: int | None = None,
) -> dict[str, Any]:
    """Inspect offline HAR 1.2 or native mitmproxy capture records without contacting recorded servers."""
    return _GLOBAL_ENGINE.har_inspect(har_path=har_path, filter_status=filter_status)


# -----------------------------------------------------------------------------
# Harness Plugin Class & IoC Lifecycle
# -----------------------------------------------------------------------------


class ReaJavaScriptPlugin(HarnessPlugin, ReaJavaScriptService):
    """Brain Harness Plugin providing JavaScript, Web, Electron, and .NET reverse engineering capabilities."""

    name = "plugin.rea_javascript"
    version = "1.0.0"
    description = (
        "REA JavaScript & Web reverse engineering: Wakaru ^1.13.0 bundle deobfuscation, "
        "Electron ASAR archive inspection, passive CDP observation, .NET managed assembly inspection, and offline HAR capture analysis."
    )
    trusted = True

    def __init__(self, engine: ReaJavaScriptEngine | None = None) -> None:
        self._engine = engine or _GLOBAL_ENGINE

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [REA_JAVASCRIPT_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(REA_JAVASCRIPT_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # Protocol Implementation Delegations
    def recover_sources(
        self,
        bundle_path: str,
        output_dir: str,
        sourcemap_path: str | None = None,
    ) -> dict[str, Any]:
        return self._engine.recover_sources(bundle_path=bundle_path, output_dir=output_dir, sourcemap_path=sourcemap_path)

    def electron_inspect(
        self,
        asar_path: str,
        extract_ipc: bool = True,
    ) -> dict[str, Any]:
        return self._engine.electron_inspect(asar_path=asar_path, extract_ipc=extract_ipc)

    def web_observe(
        self,
        cdp_endpoint: str,
        target_id: str | None = None,
        duration_ms: int = 10000,
    ) -> dict[str, Any]:
        return self._engine.web_observe(cdp_endpoint=cdp_endpoint, target_id=target_id, duration_ms=duration_ms)

    def dotnet_inspect(
        self,
        assembly_path: str,
        include_cil: bool = True,
    ) -> dict[str, Any]:
        return self._engine.dotnet_inspect(assembly_path=assembly_path, include_cil=include_cil)

    def har_inspect(
        self,
        har_path: str,
        filter_status: int | None = None,
    ) -> dict[str, Any]:
        return self._engine.har_inspect(har_path=har_path, filter_status=filter_status)


# Rule 45: Instantiated module-level singleton
plugin = ReaJavaScriptPlugin()

__all__ = [
    "ReaJavaScriptEngine",
    "ReaJavaScriptPlugin",
    "plugin",
    "rea_javascript_dotnet_inspect",
    "rea_javascript_electron_inspect",
    "rea_javascript_har_inspect",
    "rea_javascript_recover_sources",
    "rea_javascript_web_observe",
    "resolve_rea_javascript_engine",
]
