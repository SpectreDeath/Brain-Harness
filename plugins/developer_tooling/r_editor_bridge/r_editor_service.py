"""R Editor Bridge Service Implementation.

Adheres to Rule 14 (Subprocess Pipe Transport Disposal Invariant) and
Rule 53 (Subprocess Stderr Drainage & Diagnostic Surfacing Invariant).
"""

from __future__ import annotations

import asyncio
from collections import deque
import sys
from pathlib import Path
from typing import Any

import structlog

# Ensure skill scripts directory is on sys.path
_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_SKILL_SCRIPTS = _REPO_ROOT / ".agents" / "skills" / "r-language-server-toolkit" / "scripts"

if _SKILL_SCRIPTS.exists() and str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))

from r_runtime_engine import (  # type: ignore
    RDiagnosticItem,
    RLanguageServerConfig,
    RPlotEvent,
    RRuntimeDomainEngine,
    RSessionInspection,
)

from harness.services.r_runtime import (
    RDiagnosticItemData,
    RLanguageServerConfigData,
    RPlotEventData,
    RRuntimeProtocol,
    RSessionInspectionData,
)

logger = structlog.get_logger(__name__)


class REditorBridgeService(RRuntimeProtocol):
    """Implementation of RRuntimeProtocol orchestrating domain operations and sandboxed subprocess execution."""

    def __init__(self) -> None:
        self._engine = RRuntimeDomainEngine()

    def inspect_session(
        self,
        pid: int,
        working_dir: str,
        loaded_packages: list[str] | None = None,
        global_symbols: list[str] | None = None,
        active_device: str = "jgd",
    ) -> RSessionInspectionData:
        """Inspect active R process session state, namespaces, and device status."""
        inspection = self._engine.inspect_session(
            pid=pid,
            working_dir=working_dir,
            loaded_packages=loaded_packages,
            global_symbols=global_symbols,
            active_device=active_device,
        )
        return RSessionInspectionData(
            pid=inspection.pid,
            working_dir=inspection.working_dir,
            loaded_packages=list(inspection.loaded_packages),
            global_symbols=list(inspection.global_symbols),
            active_device=inspection.active_device,
            is_clean=inspection.is_clean,
        )

    def parse_diagnostics(
        self, raw_diagnostics: list[dict[str, Any]]
    ) -> list[RDiagnosticItemData]:
        """Parse raw LSP or lintr diagnostic dictionaries into normalized items."""
        items = self._engine.parse_diagnostics(raw_diagnostics)
        return [
            RDiagnosticItemData(
                file_path=item.file_path,
                line=item.line,
                column=item.column,
                severity=item.severity,
                message=item.message,
                code=item.code,
            )
            for item in items
        ]

    def stream_plot(
        self,
        plot_index: int,
        width: float,
        height: float,
        format: str = "json",
        payload_size: int = 1024,
    ) -> RPlotEventData:
        """Process and serialize an R graphics device display-list packet."""
        plot = self._engine.process_plot_event(
            plot_index=plot_index,
            width=width,
            height=height,
            format=format,
            payload_size=payload_size,
        )
        return RPlotEventData(
            plot_index=plot.plot_index,
            width=plot.width,
            height=plot.height,
            format=plot.format,
            payload_size=plot.payload_size,
            timestamp=plot.timestamp,
        )

    def validate_config(
        self,
        config: RLanguageServerConfigData,
    ) -> bool:
        """Validate R Language Server configuration parameters against safety boundaries."""
        try:
            domain_cfg = RLanguageServerConfig(
                r_path=config.r_path,
                server_args=tuple(config.server_args),
                debounce_ms=config.debounce_ms,
                lint_on_change=config.lint_on_change,
                max_payload_mb=config.max_payload_mb,
            )
            return self._engine.validate_configuration(domain_cfg)
        except (ValueError, TypeError):
            return False

    async def execute_sandboxed_r_command(
        self,
        r_path: str,
        script_args: list[str],
        timeout_seconds: float = 30.0,
    ) -> tuple[int, str, str]:
        """Execute child R subprocess within the plugin's sandboxed environment.

        Note on Nested Execution:
            When this plugin runs under SubprocessExecutor, ContainerExecutor, or VenvExecutor,
            invoking R constitutes a nested child process execution bounded by the parent sandbox's
            cgroup/process limits. It adheres strictly to Rule 14 (subprocess pipe disposal) and
            Rule 53 (asynchronous stderr ring-buffer drainage).
        """
        proc = await asyncio.create_subprocess_exec(
            r_path,
            *script_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stderr_ring: deque[str] = deque(maxlen=50)

        async def drain_stderr() -> None:
            if proc.stderr:
                while True:
                    line = await proc.stderr.readline()
                    if not line:
                        break
                    stderr_ring.append(line.decode("utf-8", errors="replace"))

        drain_task = asyncio.create_task(drain_stderr())

        try:
            stdout_data, _ = await asyncio.wait_for(
                proc.communicate(), timeout=timeout_seconds
            )
            await drain_task
            stdout_str = stdout_data.decode("utf-8", errors="replace")
            stderr_str = "".join(stderr_ring)
            return proc.returncode or 0, stdout_str, stderr_str
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            await drain_task
            stderr_str = "".join(stderr_ring)
            raise TimeoutError(
                f"R subprocess timed out after {timeout_seconds}s. Stderr trace:\n{stderr_str}"
            )
        finally:
            # Rule 14: Subprocess Pipe Transport Disposal Invariant
            if proc.stdout and not proc.stdout.at_eof():
                try:
                    proc.stdout.feed_eof()
                except Exception:
                    pass
            if proc.stderr and not proc.stderr.at_eof():
                try:
                    proc.stderr.feed_eof()
                except Exception:
                    pass
