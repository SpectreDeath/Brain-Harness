"""Slotted domain models for Webwright skill metadata and browser daemon state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SkillMetadata:
    """Metadata describing a synthesized Webwright skill."""

    skill_id: str
    template: str
    summary: str
    signature: dict[str, Any]
    output_schema: dict[str, Any]
    file_path: str
    created_at: float


@dataclass(slots=True)
class BrowserDaemonState:
    """State of persistent local Chromium browser process."""

    pid: int | None = None
    port: int = 9222
    cdp_url: str | None = None
    user_data_dir: str | None = None
    is_running: bool = False
