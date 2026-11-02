"""Agent Reach Browser Bridge Domain Engine.

Provides slotted/frozen domain models for Agent Reach multi-channel web extraction,
Schema v1 result envelopes, credential scrubbing, and session sandboxing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from typing import Any
from urllib.parse import urlparse

SCHEMA_VERSION = 1

# Codes where trying another backend cannot help
FINAL_CODES = frozenset({
    "NOT_FOUND",
    "BAD_INPUT",
    "PLATFORM_BLOCKED",
    "RATE_LIMITED",
    "NEED_LOGIN",
    "BUSY",
})

# Retryable error codes that permit fallback
RETRYABLE_CODES = frozenset({
    "TIMEOUT",
    "UPSTREAM_BROKEN",
    "NEED_SETUP",
})


@dataclass(slots=True, frozen=True)
class ReachActionQuery:
    """Immutable representation of a channel action request."""

    channel: str
    action: str
    params: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    timeout: float = 30.0

    def __post_init__(self) -> None:
        if not self.channel or not self.channel.strip():
            raise ValueError("ReachActionQuery.channel cannot be empty")
        if not self.action or not self.action.strip():
            raise ValueError("ReachActionQuery.action cannot be empty")
        if self.timeout <= 0:
            raise ValueError("ReachActionQuery.timeout must be strictly positive")


@dataclass(slots=True, frozen=True)
class ReachEnvelope:
    """Immutable representation of the unified Schema v1 result envelope."""

    schema_version: int
    ok: bool
    channel: str
    action: str
    backend: str
    items: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    meta: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    error_code: str | None = None
    error_message: str | None = None
    error_hint: str | None = None

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported schema_version: {self.schema_version}")
        if not self.channel or not self.channel.strip():
            raise ValueError("ReachEnvelope.channel cannot be empty")
        if not self.action or not self.action.strip():
            raise ValueError("ReachEnvelope.action cannot be empty")
        if not self.ok and not self.error_code:
            raise ValueError("Failed ReachEnvelope must supply an error_code")


@dataclass(slots=True, frozen=True)
class ReachChannelDescriptor:
    """Immutable metadata descriptor for a supported platform channel."""

    name: str
    level: str  # "default", "optional", "experimental"
    supported_actions: tuple[str, ...] = field(default_factory=tuple)
    url_patterns: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("ReachChannelDescriptor.name cannot be empty")
        if self.level not in ("default", "optional", "experimental"):
            raise ValueError(f"Invalid channel support level: {self.level}")


@dataclass(slots=True, frozen=True)
class ReachSessionSandbox:
    """Immutable representation of an isolated tool session directory."""

    tool: str
    session_path: str
    home_override: str
    symlink_safe: bool = True

    def __post_init__(self) -> None:
        if not self.tool or not self.tool.strip():
            raise ValueError("ReachSessionSandbox.tool cannot be empty")
        if not self.session_path or not self.session_path.strip():
            raise ValueError("ReachSessionSandbox.session_path cannot be empty")


class AgentReachDomainEngine:
    """Core domain transformations and validations for Agent Reach integration."""

    _CHANNEL_PATTERNS = {
        "youtube": (r"youtube\.com", r"youtu\.be"),
        "github": (r"github\.com",),
        "reddit": (r"reddit\.com",),
        "twitter": (r"twitter\.com", r"x\.com"),
        "bilibili": (r"bilibili\.com",),
        "xiaohongshu": (r"xiaohongshu\.com", r"xhslink\.com"),
        "boss": (r"zhipin\.com",),
        "v2ex": (r"v2ex\.com",),
        "xueqiu": (r"xueqiu\.com",),
        "xiaoyuzhou": (r"xiaoyuzhoufm\.com",),
    }

    @classmethod
    def match_channel(cls, url: str) -> str:
        """Identify matching channel for a target URL, falling back to 'web'."""
        parsed = urlparse(url)
        netloc = (parsed.netloc or "").lower()
        for channel, patterns in cls._CHANNEL_PATTERNS.items():
            if any(re.search(pat, netloc) for pat in patterns):
                return channel
        return "web"

    @staticmethod
    def scrub_credentials(text: str) -> str:
        """Redact inline URL basic authentication credentials (user:pass@host)."""
        pattern = r"(https?://)([^:\s/@]+):([^@\s/]+)@"
        return re.sub(pattern, r"\1***:***@", text)

    @staticmethod
    def build_envelope(
        ok: bool,
        channel: str,
        action: str,
        backend: str = "direct",
        items: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
        meta: dict[str, Any] | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        error_hint: str | None = None,
    ) -> ReachEnvelope:
        """Construct an immutable ReachEnvelope adhering to Schema v1."""
        meta_tuples = tuple(sorted((meta or {}).items()))
        items_tuple = tuple(items or ())

        return ReachEnvelope(
            schema_version=SCHEMA_VERSION,
            ok=ok,
            channel=channel,
            action=action,
            backend=backend,
            items=items_tuple,
            meta=meta_tuples,
            error_code=error_code,
            error_message=error_message,
            error_hint=error_hint,
        )

    @staticmethod
    def is_final_error(error_code: str) -> bool:
        """Check if error code belongs to non-retryable FINAL_CODES."""
        return error_code.upper() in FINAL_CODES

    @staticmethod
    def is_retryable_error(error_code: str) -> bool:
        """Check if error code permits trying subsequent backends in fallback cascade."""
        return error_code.upper() in RETRYABLE_CODES

