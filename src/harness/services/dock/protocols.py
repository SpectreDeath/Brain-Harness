"""Protocol definition, ServiceKey, and logger for Repository Dock."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import structlog

from harness.kernel.context import ServiceKey

from .models import (
    DockLinkRecord,
    DockManifest,
    DockRunResult,
)


logger = structlog.get_logger(__name__)


@runtime_checkable
class DockService(Protocol):
    """Protocol for Agent Dock inspection, linking, and procedure execution."""

    def inspect(self, repo_or_path: str | Path) -> DockManifest:
        """Inspect repository dock manifest without linking or state changes."""
        ...

    def link(
        self,
        repo_or_path: str | Path,
        name: str | None = None,
        approve: bool = False,
    ) -> DockLinkRecord:
        """Link an agent dock and record approval digest."""
        ...

    def list_docks(self) -> list[dict[str, Any]]:
        """List all linked docks and evaluate approval drift."""
        ...

    def tools(self, dock_name: str) -> list[str]:
        """List tools exposed by the dock."""
        ...

    async def run_async(
        self,
        dock_name: str,
        procedure_name: str,
        dry_run: bool = False,
    ) -> DockRunResult:
        """Execute declared procedure on a linked dock asynchronously."""
        ...

    def run(
        self,
        dock_name: str,
        procedure_name: str,
        dry_run: bool = False,
    ) -> DockRunResult:
        """Synchronous wrapper for procedure execution."""
        ...


DOCK_SERVICE_KEY: ServiceKey[DockService] = ServiceKey("service.dock")

__all__ = ["DockService", "DOCK_SERVICE_KEY", "logger"]
