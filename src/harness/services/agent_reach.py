"""Agent Reach Browser Bridge Service Protocol, Models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from harness.kernel.context import ServiceContext, ServiceKey


class ReachEnvelopeData(BaseModel):
    """Pydantic representation of the Schema v1 result envelope."""

    schema_version: int = Field(default=1, description="Envelope schema version (currently 1)")
    ok: bool = Field(..., description="True if operation succeeded, False otherwise")
    channel: str = Field(..., description="Target platform channel (e.g. web, youtube, github)")
    action: str = Field(..., description="Action name executed (e.g. read, search, comments)")
    backend: str = Field(default="direct", description="Underlying backend that produced result")
    items: list[dict[str, Any]] = Field(default_factory=list, description="Extracted content items")
    meta: dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")
    error: dict[str, Any] | None = Field(default=None, description="Structured error payload if ok is False")


class ReachActionQueryData(BaseModel):
    """Pydantic query request for executing a channel action."""

    channel: str = Field(..., description="Channel name to dispatch against")
    action: str = Field(..., description="Action name to invoke")
    params: dict[str, Any] = Field(default_factory=dict, description="Action-specific parameters")
    timeout: float = Field(default=30.0, description="Execution timeout in seconds")


class ReachChannelDescriptorData(BaseModel):
    """Pydantic descriptor of a platform channel's capabilities."""

    name: str = Field(..., description="Channel identifier (e.g. bilibili, reddit, web)")
    level: str = Field(default="default", description="Support level: default, optional, experimental")
    supported_actions: list[str] = Field(default_factory=list, description="List of action names")
    url_patterns: list[str] = Field(default_factory=list, description="Regex patterns for URL matching")


class ReachSessionSandboxData(BaseModel):
    """Pydantic descriptor of an isolated tool session sandbox."""

    tool: str = Field(..., description="Tool identifier (e.g. gh, yt-dlp)")
    session_path: str = Field(..., description="Private directory path for tool session")
    home_override: str = Field(..., description="HOME / USERPROFILE path override")
    symlink_safe: bool = Field(default=True, description="True if verified free of dangerous symlinks")


@runtime_checkable
class AgentReachProtocol(Protocol):
    """Service protocol for Agent Reach multi-channel web extraction and browser automation."""

    def read(
        self,
        url: str,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> ReachEnvelopeData:
        """Extract content from URL via automatic channel matching and fallback cascades."""
        ...

    def execute_action(
        self,
        channel: str,
        action: str,
        params: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> ReachEnvelopeData:
        """Execute a channel-specific action (e.g. search, comments, user info)."""
        ...

    def match_channel(self, url: str) -> str:
        """Determine the appropriate channel for a given URL."""
        ...

    def scrub_credentials(self, text: str) -> str:
        """Redact inline URL basic authentication credentials."""
        ...

    def list_channels(self) -> list[ReachChannelDescriptorData]:
        """List all supported platform channels and their capabilities."""
        ...


AGENT_REACH_SERVICE_KEY: ServiceKey[AgentReachProtocol] = ServiceKey("service.agent_reach")


def resolve_agent_reach(context: ServiceContext) -> AgentReachProtocol:
    """Resolve AgentReachProtocol service from the IoC container."""
    return context.require(AGENT_REACH_SERVICE_KEY)

