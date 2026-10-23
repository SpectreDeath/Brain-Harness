"""OpenCode Bridge Plugin implementation for Brain Harness (AGENTS.md Rule 45)."""

from __future__ import annotations

from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.opencode_bridge import (
    OPENCODE_BRIDGE_KEY,
    DefaultOpenCodeBridgeService,
    OpenCodeBridgeService,
    OpenCodeCatalogResult,
    OpenCodeRunResult,
    OpenCodeSessionResult,
    OpenCodeStatusResult,
)

logger = structlog.get_logger(__name__)


class OpenCodeBridgePlugin(HarnessPlugin, OpenCodeBridgeService):
    """Harness Plugin bridging OpenCode CLI, headless runs, and tool introspection."""

    name = "plugin.opencode_bridge"
    version = "1.0.0"
    description = "OpenCode Bridge plugin for CLI status, headless execution, and tool cataloging"
    trusted = True

    def __init__(self, cli_path: str | None = None) -> None:
        super().__init__()
        self._engine = DefaultOpenCodeBridgeService(cli_path=cli_path)

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [OPENCODE_BRIDGE_KEY]

    def on_load(self, context: ServiceContext) -> None:
        context.provide(OPENCODE_BRIDGE_KEY, self, provider=self.name)
        logger.info("OpenCodeBridgePlugin registered into IoC container")

    def on_unload(self, context: ServiceContext) -> None:
        logger.info("OpenCodeBridgePlugin unloaded from IoC container")

    def opencode_status(self) -> OpenCodeStatusResult:
        """Inspect OpenCode CLI availability, version, background server status, and active port."""
        return self._engine.get_status()

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
        return self._engine.run_prompt(
            message=message,
            directory=directory,
            model=model,
            format=format,
            auto_approve=auto_approve,
            dangerously_skip_permissions=dangerously_skip_permissions,
            timeout_seconds=timeout_seconds,
        )

    def opencode_session_info(
        self,
        action: str = "list",
        session_id: str | None = None,
    ) -> OpenCodeSessionResult:
        """Enumerate active/past OpenCode sessions or inspect session details."""
        return self._engine.get_session_info(action=action, session_id=session_id)

    def opencode_tool_catalog(self) -> OpenCodeCatalogResult:
        """List built-in OpenCode tools and active MCP servers."""
        return self._engine.get_tool_catalog()

    # Aliases
    def get_status(self) -> OpenCodeStatusResult:
        return self.opencode_status()

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
        return self.opencode_run_prompt(
            message=message,
            directory=directory,
            model=model,
            format=format,
            auto_approve=auto_approve,
            dangerously_skip_permissions=dangerously_skip_permissions,
            timeout_seconds=timeout_seconds,
        )

    def get_session_info(
        self,
        action: str = "list",
        session_id: str | None = None,
    ) -> OpenCodeSessionResult:
        return self.opencode_session_info(action=action, session_id=session_id)

    def get_tool_catalog(self) -> OpenCodeCatalogResult:
        return self.opencode_tool_catalog()


# Export authoritative module-level singleton (AGENTS.md Rule 45)
plugin = OpenCodeBridgePlugin()


# Top-level entrypoint functions for AST inspection and standalone execution
def opencode_status() -> dict[str, Any]:
    """Inspect OpenCode CLI availability, version, background server status, and active port."""
    res = plugin.opencode_status()
    return {
        "is_installed": res.is_installed,
        "version": res.version,
        "server_status": res.server_status,
        "active_port": res.active_port,
        "executable_path": res.executable_path,
        "status": res.status,
        "error": res.error,
    }


def opencode_run_prompt(
    message: str,
    directory: str | None = None,
    model: str | None = None,
    format: str = "json",
    auto_approve: bool = True,
    dangerously_skip_permissions: bool = False,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    """Execute a headless non-interactive instruction through OpenCode CLI."""
    res = plugin.opencode_run_prompt(
        message=message,
        directory=directory,
        model=model,
        format=format,
        auto_approve=auto_approve,
        dangerously_skip_permissions=dangerously_skip_permissions,
        timeout_seconds=timeout_seconds,
    )
    return {
        "exit_code": res.exit_code,
        "output": res.output,
        "status": res.status,
        "duration_ms": res.duration_ms,
        "parsed_json": res.parsed_json,
        "error": res.error,
    }


def opencode_session_info(
    action: str = "list",
    session_id: str | None = None,
) -> dict[str, Any]:
    """Enumerate active/past OpenCode sessions or inspect session details."""
    res = plugin.opencode_session_info(action=action, session_id=session_id)
    return {
        "sessions": list(res.sessions),
        "active_session": res.active_session,
        "status": res.status,
        "error": res.error,
    }


def opencode_tool_catalog() -> dict[str, Any]:
    """List built-in OpenCode tools and active MCP servers."""
    res = plugin.opencode_tool_catalog()
    return {
        "tools_count": res.tools_count,
        "tools": list(res.tools),
        "mcp_servers": list(res.mcp_servers),
        "status": res.status,
        "error": res.error,
    }
