"""Agent Desktop service protocol, slotted domain models, and ServiceKey."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


# -----------------------------------------------------------------------------
# Slotted & Frozen Value Objects (Rule 12 & Rule 43)
# -----------------------------------------------------------------------------

class EvidenceTriState(str, Enum):
    """Tri-state property observation model (Known | Absent | Unknown).

    Never collapse Unknown to Absent (or boolean False in negative position),
    preserving the distinction between 'queried and confirmed absent' and
    'read timed out or failed'.
    """

    KNOWN = "known"
    ABSENT = "absent"
    UNKNOWN = "unknown"

    def is_known(self) -> bool:
        return self == EvidenceTriState.KNOWN

    def is_absent(self) -> bool:
        return self == EvidenceTriState.ABSENT

    def is_unknown(self) -> bool:
        return self == EvidenceTriState.UNKNOWN


_REF_PATTERN = re.compile(r"^@(?P<snapshot_id>[a-zA-Z0-9_-]+):e(?P<index>\d+)$")


@dataclass(slots=True, frozen=True)
class DesktopRefToken:
    """Immutable qualified element reference token: @<snapshot_id>:e<N>.

    Bare tokens (e.g. '@e8') are refused with ValueError to prevent cross-snapshot
    ambiguity and stale element mutations.
    """

    snapshot_id: str
    element_index: int
    qualified: str

    def __post_init__(self) -> None:
        if not self.snapshot_id or not self.snapshot_id.strip():
            raise ValueError("DesktopRefToken requires a non-empty snapshot_id")
        if self.element_index < 0:
            raise ValueError("DesktopRefToken element_index must be non-negative")
        if not self.qualified or not _REF_PATTERN.match(self.qualified):
            raise ValueError(
                f"Invalid qualified ref '{self.qualified}'. Must match '@<snapshot_id>:e<N>'"
            )

    @classmethod
    def parse(cls, ref_str: str) -> DesktopRefToken:
        """Parse and validate a ref string into a DesktopRefToken."""
        if not ref_str or not isinstance(ref_str, str):
            raise ValueError("Reference string must be a non-empty string")
        match = _REF_PATTERN.match(ref_str.strip())
        if not match:
            raise ValueError(
                f"Ref '{ref_str}' is invalid. Bare refs like '@e8' are refused; must be '@<snapshot_id>:e<N>'"
            )
        snapshot_id = match.group("snapshot_id")
        index = int(match.group("index"))
        return cls(snapshot_id=snapshot_id, element_index=index, qualified=ref_str.strip())

    def powershell_quoted(self) -> str:
        """Return single-quoted token for PowerShell to prevent splatting."""
        return f"'{self.qualified}'"


@dataclass(slots=True, frozen=True)
class ActionDisposition:
    """2D outcome matrix separating delivery outcome from retry safety.

    Prevents double-clicking or re-submitting non-idempotent form actions when
    delivery is uncertain or unverified.
    """

    delivery: str = "unknown"
    retry: str = "unknown"

    def __post_init__(self) -> None:
        valid_delivery = {
            "unknown",
            "not_delivered",
            "delivery_uncertain",
            "delivered_unverified",
            "delivered_verified",
        }
        valid_retry = {"unknown", "safe", "unsafe"}
        if self.delivery not in valid_delivery:
            raise ValueError(f"Invalid delivery disposition: {self.delivery}")
        if self.retry not in valid_retry:
            raise ValueError(f"Invalid retry disposition: {self.retry}")

    @property
    def is_retry_safe(self) -> bool:
        """True only if the action was confirmed safe to retry."""
        return self.retry == "safe"

    @property
    def should_rollback_transaction(self) -> bool:
        """True if the transaction made uncertain mutations or cannot be retried safely."""
        return self.delivery in ("delivery_uncertain", "delivered_unverified") or self.retry == "unsafe"


# -----------------------------------------------------------------------------
# Pydantic Service Result Envelopes
# -----------------------------------------------------------------------------

class AgentDesktopSnapshotResult(BaseModel):
    """Result of observing an application accessibility tree."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    version: str = Field(default="2.6", description="Envelope protocol version")
    snapshot_id: str = Field(default="", description="Snapshot identifier for allocating refs")
    app: str = Field(default="", description="Target application name")
    ref_count: int = Field(default=0, description="Total actionable refs allocated")
    complete: bool = Field(default=True, description="Whether full tree walk completed within budget")
    tree: dict[str, Any] = Field(default_factory=dict, description="Observed hierarchical accessibility tree")
    surfaces: list[str] = Field(default_factory=list, description="Active UI surfaces (e.g. window, menu, sheet)")
    error: str | None = Field(default=None, description="Error explanation if observation failed")
    suggestion: str | None = Field(default=None, description="Recovery suggestion if failed")


class AgentDesktopActResult(BaseModel):
    """Result of executing an action on a desktop element ref."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    ok: bool = Field(default=True, description="Whether action succeeded")
    command: str = Field(default="", description="Command executed (click, set-value, etc.)")
    ref_id: str = Field(default="", description="Target qualified element ref")
    delivery_disposition: str = Field(default="unknown", description="Delivery outcome")
    retry_disposition: str = Field(default="unknown", description="Retry safety disposition")
    retry_safe: bool = Field(default=True, description="Direct convenience boolean for safe retry")
    steps: list[dict[str, Any]] = Field(default_factory=list, description="Activation chain steps")
    surfaces: list[str] = Field(default_factory=list, description="Active UI surfaces after action")
    error_code: str | None = Field(default=None, description="Standard error code (e.g. STALE_REF, AMBIGUOUS_TARGET)")
    error_message: str | None = Field(default=None, description="Error message if failed")
    suggestion: str | None = Field(default=None, description="Action recovery suggestion")


class AgentDesktopWindowResult(BaseModel):
    """Result of window and display discovery or management."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    windows: list[dict[str, Any]] = Field(default_factory=list, description="Discovered windows")
    displays: list[dict[str, Any]] = Field(default_factory=list, description="Discovered monitors/displays")
    apps: list[str] = Field(default_factory=list, description="Running desktop applications")
    error: str | None = Field(default=None, description="Error message if failed")


class AgentDesktopStatusResult(BaseModel):
    """Status of agent-desktop runtime, permissions, and supported surfaces."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    platform: str = Field(default="windows", description="Host OS platform (windows, macos, linux)")
    permissions_granted: bool = Field(default=True, description="Whether OS accessibility permissions are active")
    accessibility_api: str = Field(default="UI Automation", description="Native OS accessibility API")
    supported_surfaces: list[str] = Field(
        default_factory=lambda: ["window", "menu", "dialog", "sheet", "alert"],
        description="Supported desktop surfaces",
    )
    binary_available: bool = Field(default=True, description="Whether agent-desktop binary or MCP server is available")
    execution_mode: str = Field(default="cli_subprocess", description="Runtime mode: cli_subprocess, mcp_stdio, or simulation")
    error: str | None = Field(default=None, description="Error explanation if status check failed")


# -----------------------------------------------------------------------------
# Service Protocol (Rule 49)
# -----------------------------------------------------------------------------

@runtime_checkable
class AgentDesktopService(Protocol):
    """Protocol for Agent Desktop native accessibility tree observation and computer-use automation."""

    async def snapshot(
        self,
        app: str = "",
        root_ref: str = "",
        interactive_only: bool = True,
        skeleton: bool = False,
        compact: bool = True,
        surface: str = "",
        session: str = "default",
    ) -> AgentDesktopSnapshotResult:
        """Capture an accessibility tree snapshot of an application or drill into a root ref."""
        ...

    async def act(
        self,
        action: str,
        ref_id: str,
        value: str = "",
        headed: bool = False,
        interval_ms: int | None = None,
        session: str = "default",
    ) -> AgentDesktopActResult:
        """Perform a semantic or physical action (click, set-value, type, select) on an element ref."""
        ...

    async def find(
        self,
        app: str = "",
        role: str = "",
        name: str = "",
        text: str = "",
        session: str = "default",
    ) -> AgentDesktopSnapshotResult:
        """Find elements matching role, accessible name, or text within an application."""
        ...

    async def manage_window(
        self,
        operation: str,
        app: str = "",
        window_id: str = "",
        bounds: dict[str, int] | None = None,
    ) -> AgentDesktopWindowResult:
        """List, focus, resize, or move application windows."""
        ...

    async def wait_for(
        self,
        app: str = "",
        element_ref: str = "",
        window_title: str = "",
        text: str = "",
        timeout_ms: int = 5000,
    ) -> dict[str, Any]:
        """Wait for an accessibility element, window, surface, or text condition without fixed sleeps."""
        ...

    async def get_status(
        self,
        check_permissions: bool = True,
    ) -> AgentDesktopStatusResult:
        """Query host platform status, accessibility permissions, and binary availability."""
        ...


AGENT_DESKTOP_KEY: ServiceKey[AgentDesktopService] = ServiceKey("service.agent_desktop")
