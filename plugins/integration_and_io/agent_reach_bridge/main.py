"""Agent Reach Bridge Plugin entrypoint and tool dispatch."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

# Ensure paths are added
_PLUGIN_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _PLUGIN_DIR.parents[2]
_SKILL_SCRIPTS = _REPO_ROOT / ".agents" / "skills" / "agent-reach-browser-bridge" / "scripts"
_HARNESS_SRC = _REPO_ROOT / "src"

for _p in [_SKILL_SCRIPTS, _HARNESS_SRC]:
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.agent_reach import (
    AGENT_REACH_SERVICE_KEY,
    AgentReachProtocol,
    ReachChannelDescriptorData,
    ReachEnvelopeData,
)
try:
    from plugins.integration_and_io.agent_reach_bridge.agent_reach_service import AgentReachBridgeService
except ImportError:
    from agent_reach_service import AgentReachBridgeService

logger = structlog.get_logger(__name__)


class AgentReachBridgePlugin(HarnessPlugin, AgentReachProtocol):
    """Bridge plugin providing multi-platform web extraction, CDP browser automation, and Schema v1 envelopes."""

    def __init__(self) -> None:
        super().__init__()
        self._service = AgentReachBridgeService()

    @property
    def name(self) -> str:
        return "plugin.agent_reach_bridge"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Agent Reach bridge integrating multi-platform web extraction, "
            "stealth CloakBrowser CDP sessions, and Schema v1 result envelopes"
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [AGENT_REACH_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        """Register self as AgentReachProtocol service into IoC container."""
        context.provide(AGENT_REACH_SERVICE_KEY, self)
        logger.info(
            "agent_reach_service_provided",
            service=str(AGENT_REACH_SERVICE_KEY),
        )

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()

    # --- AgentReachProtocol Delegation ---

    def read(
        self,
        url: str,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> ReachEnvelopeData:
        return self._service.read(url=url, timeout=timeout, **kwargs)

    def execute_action(
        self,
        channel: str,
        action: str,
        params: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> ReachEnvelopeData:
        return self._service.execute_action(
            channel=channel, action=action, params=params, timeout=timeout
        )

    def match_channel(self, url: str) -> str:
        return self._service.match_channel(url)

    def scrub_credentials(self, text: str) -> str:
        return self._service.scrub_credentials(text)

    def list_channels(self) -> list[ReachChannelDescriptorData]:
        return self._service.list_channels()


# Rule 45: Export module singleton plugin instance
plugin = AgentReachBridgePlugin()


# Top-level entrypoints matching plugin.json declarations
def reach_read(
    url: str,
    timeout: float = 30.0,
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level entrypoint for reading web or platform URL."""
    res = plugin.read(url=url, timeout=timeout, **kwargs)
    return res.model_dump()


def reach_action(
    channel: str,
    action: str,
    params: dict[str, Any] | None = None,
    timeout: float = 30.0,
    **kwargs: Any,
) -> dict[str, Any]:
    """Top-level entrypoint for executing platform action."""
    res = plugin.execute_action(
        channel=channel, action=action, params=params, timeout=timeout
    )
    return res.model_dump()


def reach_inspect_channels(**kwargs: Any) -> list[dict[str, Any]]:
    """Top-level entrypoint for inspecting registered platform channels."""
    channels = plugin.list_channels()
    return [c.model_dump() for c in channels]


def reach_scrub_url(text: str, **kwargs: Any) -> str:
    """Top-level entrypoint for redacting basic authentication credentials."""
    return plugin.scrub_credentials(text)
