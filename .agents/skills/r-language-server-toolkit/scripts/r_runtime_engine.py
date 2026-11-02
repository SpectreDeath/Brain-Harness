"""R Runtime & Language Server Domain Engine.

Provides slotted/frozen domain models for R language server protocol interactions,
C-level graphics device packet processing (jgd), and session watcher reflection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import time
from typing import Any


@dataclass(slots=True, frozen=True)
class RDiagnosticItem:
    """Immutable representation of an R language server diagnostic item."""

    file_path: str
    line: int
    column: int
    severity: str
    message: str
    code: str | None = None

    def __post_init__(self) -> None:
        if not self.file_path or not self.file_path.strip():
            raise ValueError("RDiagnosticItem.file_path cannot be empty")
        if self.line < 0:
            raise ValueError("RDiagnosticItem.line must be non-negative (0-indexed)")
        if self.column < 0:
            raise ValueError("RDiagnosticItem.column must be non-negative (0-indexed)")
        if self.severity not in ("Error", "Warning", "Information", "Hint"):
            raise ValueError(f"Invalid diagnostic severity: {self.severity}")
        if not self.message or not self.message.strip():
            raise ValueError("RDiagnosticItem.message cannot be empty")


@dataclass(slots=True, frozen=True)
class RSessionInspection:
    """Immutable representation of an active R runtime session reflection."""

    pid: int
    working_dir: str
    loaded_packages: tuple[str, ...] = field(default_factory=tuple)
    global_symbols: tuple[str, ...] = field(default_factory=tuple)
    active_device: str = "jgd"
    is_clean: bool = True

    def __post_init__(self) -> None:
        if self.pid <= 0:
            raise ValueError("RSessionInspection.pid must be positive")
        if not self.working_dir or not self.working_dir.strip():
            raise ValueError("RSessionInspection.working_dir cannot be empty")


@dataclass(slots=True, frozen=True)
class RPlotEvent:
    """Immutable packet from C-level graphics device serialization."""

    plot_index: int
    width: float
    height: float
    format: str
    payload_size: int
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.plot_index < 0:
            raise ValueError("RPlotEvent.plot_index must be non-negative")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Plot dimensions must be strictly positive")
        if self.format not in ("json", "svg", "png"):
            raise ValueError(f"Unsupported plot format: {self.format}")
        if self.payload_size < 0:
            raise ValueError("payload_size cannot be negative")


@dataclass(slots=True, frozen=True)
class RLanguageServerConfig:
    """Immutable configuration for launching and managing R Language Server."""

    r_path: str
    server_args: tuple[str, ...] = field(default_factory=tuple)
    debounce_ms: int = 300
    lint_on_change: bool = True
    max_payload_mb: int = 10

    def __post_init__(self) -> None:
        if not self.r_path or not self.r_path.strip():
            raise ValueError("RLanguageServerConfig.r_path cannot be empty")
        if self.debounce_ms < 50:
            raise ValueError("debounce_ms must be at least 50ms to prevent thrashing")
        if self.max_payload_mb <= 0:
            raise ValueError("max_payload_mb must be strictly positive")


class RRuntimeDomainEngine:
    """Core domain engine for R language server, graphics, and session operations."""

    @staticmethod
    def inspect_session(
        pid: int,
        working_dir: str,
        loaded_packages: list[str] | tuple[str, ...] | None = None,
        global_symbols: list[str] | tuple[str, ...] | None = None,
        active_device: str = "jgd",
    ) -> RSessionInspection:
        """Inspect and construct an immutable RSessionInspection report."""
        packages = tuple(sorted(set(loaded_packages or ())))
        symbols = tuple(sorted(set(global_symbols or ())))
        
        # Check environment cleanliness: ensures .vsc internals haven't leaked into symbols
        is_clean = not any(s.startswith(".vsc") for s in symbols)

        return RSessionInspection(
            pid=pid,
            working_dir=working_dir,
            loaded_packages=packages,
            global_symbols=symbols,
            active_device=active_device,
            is_clean=is_clean,
        )

    @staticmethod
    def parse_diagnostics(raw_diagnostics: list[dict[str, Any]]) -> tuple[RDiagnosticItem, ...]:
        """Parse raw LSP or lintr diagnostic dictionaries into normalized RDiagnosticItem entities."""
        severity_map = {
            1: "Error",
            2: "Warning",
            3: "Information",
            4: "Hint",
            "error": "Error",
            "warning": "Warning",
            "info": "Information",
            "style": "Information",
            "hint": "Hint",
        }

        items: list[RDiagnosticItem] = []
        for diag in raw_diagnostics:
            file_path = str(diag.get("file_path") or diag.get("uri") or "unknown.R")
            
            # Handle LSP range object vs flat line/col
            range_obj = diag.get("range", {})
            start_pos = range_obj.get("start", {}) if isinstance(range_obj, dict) else {}
            line = start_pos.get("line", diag.get("line", 0))
            column = start_pos.get("character", diag.get("column", 0))

            raw_sev = diag.get("severity", 1)
            severity = severity_map.get(raw_sev, "Warning") if not isinstance(raw_sev, str) else severity_map.get(raw_sev.lower(), "Warning")
            message = str(diag.get("message") or "Diagnostic notice")
            code = str(diag.get("code")) if diag.get("code") is not None else None

            items.append(
                RDiagnosticItem(
                    file_path=file_path,
                    line=int(line),
                    column=int(column),
                    severity=severity,
                    message=message,
                    code=code,
                )
            )

        return tuple(items)

    @staticmethod
    def process_plot_event(
        plot_index: int,
        width: float,
        height: float,
        format: str = "json",
        payload_size: int = 1024,
    ) -> RPlotEvent:
        """Process and construct an immutable RPlotEvent packet."""
        return RPlotEvent(
            plot_index=plot_index,
            width=float(width),
            height=float(height),
            format=format,
            payload_size=payload_size,
        )

    @staticmethod
    def validate_configuration(config: RLanguageServerConfig) -> bool:
        """Validate RLanguageServerConfig parameters against operational safety boundaries."""
        if not config.r_path:
            return False
        if config.debounce_ms < 50 or config.debounce_ms > 5000:
            return False
        if config.max_payload_mb > 50:
            return False
        return True

