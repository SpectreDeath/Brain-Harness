"""Stagehand Browser Plugin Entrypoint & Service Implementation."""

from __future__ import annotations

from typing import Any
import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.stagehand_browser import (
    STAGEHAND_BROWSER_KEY,
    StagehandActResult,
    StagehandBrowserService,
    StagehandExtractResult,
    StagehandObserveElement,
    StagehandObserveResult,
    StagehandSessionStatus,
    StagehandWebMCPResult,
)

from .engine import StagehandBrowserEngine

logger = structlog.get_logger(__name__)

_GLOBAL_ENGINE = StagehandBrowserEngine()


def _get_engine() -> StagehandBrowserEngine:
    return _GLOBAL_ENGINE


# -----------------------------------------------------------------------------
# Tool Handlers (Standalone Functions for Tool Registry)
# -----------------------------------------------------------------------------

def stagehand_act(
    action: str,
    model: str = "gpt-4o",
    timeout_s: int = 30,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute high-level natural language actions (clicks, keyboard input, navigation) on active page."""
    engine = _get_engine()
    return engine.act(action=action, model=model, timeout_s=timeout_s, variables=variables)


def stagehand_extract(
    instruction: str,
    schema: dict[str, Any],
    model: str = "gpt-4o",
    use_text_extract: bool = False,
) -> dict[str, Any]:
    """Extract structured data matching a target JSON schema directly from live DOM & rendered layout."""
    engine = _get_engine()
    return engine.extract(instruction=instruction, schema=schema, model=model, use_text_extract=use_text_extract)


def stagehand_observe(
    instruction: str = "",
    model: str = "gpt-4o",
    return_action: bool = True,
) -> dict[str, Any]:
    """Inspect live DOM to return interactive elements, locators, and suggested next actions."""
    engine = _get_engine()
    return engine.observe(instruction=instruction, model=model, return_action=return_action)


def stagehand_webmcp_tool_invoke(
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    page_id: str = "active",
) -> dict[str, Any]:
    """Discover and invoke WebMCP (Web Model Context Protocol) tools exposed by web pages."""
    engine = _get_engine()
    return engine.invoke_webmcp_tool(tool_name=tool_name, arguments=arguments, page_id=page_id)


def stagehand_session_control(
    action: str,
    url: str = "",
    script: str = "",
    provider: str = "local",
) -> dict[str, Any]:
    """Manage browser session lifecycle, navigation, JavaScript evaluation, and page capture."""
    engine = _get_engine()
    return engine.control_session(action=action, url=url, script=script, provider=provider)


# -----------------------------------------------------------------------------
# Plugin Class
# -----------------------------------------------------------------------------

class StagehandBrowserPlugin(HarnessPlugin, StagehandBrowserService):
    """Harness Plugin providing Stagehand Next-Gen Browser Automation, Act, Extract, Observe, and WebMCP."""

    name = "plugin.stagehand_browser"
    version = "1.0.0"
    description = "Browserbase's next-generation AI browser automation engine with Act, Extract, Observe, and WebMCP protocol"
    trusted = True

    def __init__(self) -> None:
        self._engine = _get_engine()

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [STAGEHAND_BROWSER_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(STAGEHAND_BROWSER_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    async def on_unload(self) -> None:
        logger.info("unloading_plugin", plugin=self.name)

    # -------------------------------------------------------------------------
    # StagehandBrowserService Protocol Implementation
    # -------------------------------------------------------------------------

    async def act(
        self,
        action: str,
        model: str = "gpt-4o",
        timeout_s: int = 30,
        variables: dict[str, Any] | None = None,
    ) -> StagehandActResult:
        res = self._engine.act(action=action, model=model, timeout_s=timeout_s, variables=variables)
        return StagehandActResult(**res)

    async def extract(
        self,
        instruction: str,
        schema: dict[str, Any],
        model: str = "gpt-4o",
        use_text_extract: bool = False,
    ) -> StagehandExtractResult:
        res = self._engine.extract(
            instruction=instruction, schema=schema, model=model, use_text_extract=use_text_extract
        )
        return StagehandExtractResult(**res)

    async def observe(
        self,
        instruction: str = "",
        model: str = "gpt-4o",
        return_action: bool = True,
    ) -> StagehandObserveResult:
        res = self._engine.observe(instruction=instruction, model=model, return_action=return_action)
        elems = [StagehandObserveElement(**e) for e in res["elements"]]
        return StagehandObserveResult(
            status=res["status"],
            elements=elems,
            page_title=res["page_title"],
            url=res["url"],
            error=res["error"],
        )

    async def invoke_webmcp_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        page_id: str = "active",
    ) -> StagehandWebMCPResult:
        res = self._engine.invoke_webmcp_tool(tool_name=tool_name, arguments=arguments, page_id=page_id)
        return StagehandWebMCPResult(**res)

    async def control_session(
        self,
        action: str,
        url: str = "",
        script: str = "",
        provider: str = "local",
    ) -> StagehandSessionStatus:
        res = self._engine.control_session(action=action, url=url, script=script, provider=provider)
        return StagehandSessionStatus(**res)
