"""Stagehand Browser service protocol, typed result models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class StagehandActResult(BaseModel):
    """Result of executing natural language action on web page."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    success: bool = Field(default=True, description="Whether action succeeded")
    action_performed: str = Field(..., description="Action description executed")
    message: str = Field(default="", description="Diagnostic details or confirmation")
    error: str | None = Field(default=None, description="Error explanation if action failed")


class StagehandExtractResult(BaseModel):
    """Result of extracting structured data from web page DOM."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    data: dict[str, Any] | list[Any] = Field(default_factory=dict, description="Extracted JSON data matching schema")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extraction metadata")
    error: str | None = Field(default=None, description="Error explanation if extraction failed")


class StagehandObserveElement(BaseModel):
    """Interactive element discovered by observe."""

    selector: str = Field(..., description="DOM CSS/XPath or backend locator identifier")
    description: str = Field(..., description="Element purpose and label")
    action_suggested: str = Field(default="", description="Suggested natural language interaction")
    backend_node_id: int | None = Field(default=None, description="CDP backend node identifier")


class StagehandObserveResult(BaseModel):
    """Result of observing page state and actionable elements."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    elements: list[StagehandObserveElement] = Field(default_factory=list, description="Discovered interactive elements")
    page_title: str = Field(default="", description="Current page title")
    url: str = Field(default="", description="Current page URL")
    error: str | None = Field(default=None, description="Error explanation if observation failed")


class StagehandWebMCPResult(BaseModel):
    """Result of discovering or invoking a WebMCP tool on a web page."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    invocation_id: str = Field(default="", description="Invocation tracking identifier")
    invocation_status: str = Field(default="Completed", description="Status: Completed, Canceled, Error")
    output: Any | None = Field(default=None, description="Tool execution return value")
    available_tools: list[dict[str, Any]] = Field(default_factory=list, description="Available WebMCP tools when listed")
    error_text: str | None = Field(default=None, description="Error text if failed")


class StagehandSessionStatus(BaseModel):
    """Status and control metadata of a Stagehand browser session."""

    status: str = Field(default="ok", description="Status indicator (ok, closed, error)")
    session_id: str = Field(..., description="Unique browser session identifier")
    provider: str = Field(default="local", description="Provider: local (CDP) or browserbase (Cloud)")
    current_url: str = Field(default="", description="Active page URL")
    page_title: str = Field(default="", description="Active page title")
    screenshot_b64: str | None = Field(default=None, description="Base64 encoded screenshot if requested")
    eval_result: Any | None = Field(default=None, description="JavaScript evaluation result if applicable")
    error: str | None = Field(default=None, description="Error explanation if operation failed")


@runtime_checkable
class StagehandBrowserService(Protocol):
    """Protocol for Stagehand next-gen browser automation, Act, Extract, Observe, and WebMCP."""

    async def act(
        self,
        action: str,
        model: str = "gpt-4o",
        timeout_s: int = 30,
        variables: dict[str, Any] | None = None,
    ) -> StagehandActResult:
        """Execute high-level natural language actions (clicks, keyboard input, navigation) on active page."""
        ...

    async def extract(
        self,
        instruction: str,
        schema: dict[str, Any],
        model: str = "gpt-4o",
        use_text_extract: bool = False,
    ) -> StagehandExtractResult:
        """Extract structured data matching a target JSON schema directly from live DOM & rendered layout."""
        ...

    async def observe(
        self,
        instruction: str = "",
        model: str = "gpt-4o",
        return_action: bool = True,
    ) -> StagehandObserveResult:
        """Inspect live DOM to return interactive elements, locators, and suggested next actions."""
        ...

    async def invoke_webmcp_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        page_id: str = "active",
    ) -> StagehandWebMCPResult:
        """Discover and invoke WebMCP (Web Model Context Protocol) tools exposed by web pages."""
        ...

    async def control_session(
        self,
        action: str,
        url: str = "",
        script: str = "",
        provider: str = "local",
    ) -> StagehandSessionStatus:
        """Manage browser session lifecycle, navigation, JavaScript evaluation, and page capture."""
        ...


STAGEHAND_BROWSER_KEY: ServiceKey[StagehandBrowserService] = ServiceKey("service.stagehand_browser")
