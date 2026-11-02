"""R Editor Bridge Plugin entrypoint and tool dispatch."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Ensure paths are added
_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_SKILL_SCRIPTS = _REPO_ROOT / ".agents" / "skills" / "r-language-server-toolkit" / "scripts"
_HARNESS_SRC = _REPO_ROOT / "src"

for _p in [_SKILL_SCRIPTS, _HARNESS_SRC]:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.r_runtime import (
    R_RUNTIME_SERVICE_KEY,
    RDiagnosticItemData,
    RLanguageServerConfigData,
    RPlotEventData,
    RRuntimeProtocol,
    RSessionInspectionData,
)
try:
    from plugins.developer_tooling.r_editor_bridge.r_editor_service import REditorBridgeService
except ImportError:
    from r_editor_service import REditorBridgeService

logger = structlog.get_logger(__name__)


class REditorBridgePlugin(HarnessPlugin, RRuntimeProtocol):
    """Bridge plugin providing R runtime inspection, LSP diagnostics, and graphics streaming."""

    def __init__(self) -> None:
        super().__init__()
        self._service = REditorBridgeService()

    @property
    def name(self) -> str:
        return "plugin.r_editor_bridge"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "R editor tooling bridge integrating languageserver LSP 3.17, "
            "jgd C-level graphics streaming, and session watcher reflection"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [R_RUNTIME_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register self as the RRuntimeProtocol service into IoC container."""
        context.provide(R_RUNTIME_SERVICE_KEY, self)
        logger.info(
            "r_runtime_service_provided",
            service=str(R_RUNTIME_SERVICE_KEY),
        )

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    # --- RRuntimeProtocol Delegation ---

    def inspect_session(
        self,
        pid: int,
        working_dir: str,
        loaded_packages: list[str] | None = None,
        global_symbols: list[str] | None = None,
        active_device: str = "jgd",
    ) -> RSessionInspectionData:
        return self._service.inspect_session(
            pid=pid,
            working_dir=working_dir,
            loaded_packages=loaded_packages,
            global_symbols=global_symbols,
            active_device=active_device,
        )

    def parse_diagnostics(
        self, raw_diagnostics: list[dict[str, Any]]
    ) -> list[RDiagnosticItemData]:
        return self._service.parse_diagnostics(raw_diagnostics)

    def stream_plot(
        self,
        plot_index: int,
        width: float,
        height: float,
        format: str = "json",
        payload_size: int = 1024,
    ) -> RPlotEventData:
        return self._service.stream_plot(
            plot_index=plot_index,
            width=width,
            height=height,
            format=format,
            payload_size=payload_size,
        )

    def validate_config(
        self,
        config: RLanguageServerConfigData,
    ) -> bool:
        return self._service.validate_config(config)


# Rule 45: Export module singleton plugin instance
plugin = REditorBridgePlugin()


# Top-level entrypoints matching plugin.json declarations
def r_inspect_session(
    pid: int,
    working_dir: str,
    loaded_packages: list[str] | None = None,
    global_symbols: list[str] | None = None,
    active_device: str = "jgd",
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level entrypoint for inspecting R session state."""
    res = plugin.inspect_session(
        pid=pid,
        working_dir=working_dir,
        loaded_packages=loaded_packages,
        global_symbols=global_symbols,
        active_device=active_device,
    )
    return res.model_dump()


def r_parse_diagnostics(
    raw_diagnostics: list[dict[str, Any]],
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Top-level entrypoint for parsing R language server diagnostics."""
    items = plugin.parse_diagnostics(raw_diagnostics)
    return [i.model_dump() for i in items]


def r_stream_plot(
    plot_index: int,
    width: float,
    height: float,
    format: str = "json",
    payload_size: int = 1024,
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level entrypoint for processing plot display-list packets."""
    plot = plugin.stream_plot(
        plot_index=plot_index,
        width=width,
        height=height,
        format=format,
        payload_size=payload_size,
    )
    return plot.model_dump()


def r_validate_config(
    r_path: str,
    server_args: list[str] | None = None,
    debounce_ms: int = 300,
    lint_on_change: bool = True,
    max_payload_mb: int = 10,
    **kwargs: Any,
) -> bool:
    """Top-level entrypoint for validating R language server configuration."""
    cfg = RLanguageServerConfigData(
        r_path=r_path,
        server_args=server_args or [],
        debounce_ms=debounce_ms,
        lint_on_change=lint_on_change,
        max_payload_mb=max_payload_mb,
    )
    return plugin.validate_config(cfg)

