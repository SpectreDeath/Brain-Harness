"""Service protocol and ServiceKey for OpenCode Bridge service (AGENTS.md Rule 2 & 49)."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from harness.kernel.context import ServiceKey
from .models import (
    OpenCodeCatalogResult,
    OpenCodeRunResult,
    OpenCodeSessionResult,
    OpenCodeStatusResult,
)


@runtime_checkable
class OpenCodeBridgeService(Protocol):
    """Protocol for OpenCode CLI inspection, headless execution, and catalog management."""

    def opencode_status(self) -> OpenCodeStatusResult:
        """Inspect OpenCode CLI availability, version, background server status, and active port."""
        ...

    def opencode_run_prompt(
        self,
        message: str,
        directory: str | None = None,
        model: str | None = None,
        format: str = "json",
        auto_approve: bool = True,
        dangerously_skip_permissions: bool = False,
        timeout_seconds: int = 60,
    ) -> OpenCodeRunResult:
        """Execute a headless non-interactive instruction through OpenCode CLI."""
        ...

    def opencode_session_info(
        self,
        action: str = "list",
        session_id: str | None = None,
    ) -> OpenCodeSessionResult:
        """Enumerate active/past OpenCode sessions or inspect session details."""
        ...

    def opencode_tool_catalog(self) -> OpenCodeCatalogResult:
        """List built-in OpenCode tools and active MCP servers."""
        ...

    # Backward-compatible convenience aliases
    def get_status(self) -> OpenCodeStatusResult:
        ...

    def run_prompt(
        self,
        message: str,
        directory: str | None = None,
        model: str | None = None,
        format: str = "json",
        auto_approve: bool = True,
        dangerously_skip_permissions: bool = False,
        timeout_seconds: int = 60,
    ) -> OpenCodeRunResult:
        ...

    def get_session_info(
        self,
        action: str = "list",
        session_id: str | None = None,
    ) -> OpenCodeSessionResult:
        ...

    def get_tool_catalog(self) -> OpenCodeCatalogResult:
        ...


OPENCODE_BRIDGE_KEY: ServiceKey[OpenCodeBridgeService] = ServiceKey("service.opencode_bridge")
