"""Slotted and frozen data models for OpenCode Bridge service (AGENTS.md Rule 12)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class OpenCodeStatusResult:
    """Slotted and immutable record of OpenCode installation and daemon status."""

    is_installed: bool
    version: str | None = None
    server_status: str = "stopped"
    active_port: int | None = None
    executable_path: str | None = None
    status: str = "ok"
    error: str | None = None

    def __post_init__(self) -> None:
        assert self.status in ("ok", "error", "cli_not_found"), f"Invalid status: {self.status}"


@dataclass(slots=True, frozen=True)
class OpenCodeRunResult:
    """Slotted and immutable record of an executed OpenCode prompt instruction."""

    exit_code: int
    output: str
    status: str = "ok"
    duration_ms: float = 0.0
    parsed_json: dict[str, Any] | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        assert self.duration_ms >= 0.0, f"Negative duration: {self.duration_ms}"


@dataclass(slots=True, frozen=True)
class OpenCodeSessionResult:
    """Slotted and immutable record of OpenCode sessions query."""

    sessions: tuple[dict[str, Any], ...] = ()
    active_session: dict[str, Any] | None = None
    status: str = "ok"
    error: str | None = None

    def __post_init__(self) -> None:
        assert self.status in ("ok", "error"), f"Invalid status: {self.status}"


@dataclass(slots=True, frozen=True)
class OpenCodeCatalogResult:
    """Slotted and immutable catalog of OpenCode tools and MCP servers."""

    tools_count: int
    tools: tuple[dict[str, Any], ...] = ()
    mcp_servers: tuple[str, ...] = ()
    status: str = "ok"
    error: str | None = None

    def __post_init__(self) -> None:
        assert self.tools_count >= 0, f"Negative tools_count: {self.tools_count}"
