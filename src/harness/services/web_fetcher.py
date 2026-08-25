"""Web fetcher and Markdown distillation protocol, typed models, and ServiceKey."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field

from harness.kernel.context import ServiceKey


class WebFetchResult(BaseModel):
    """Result of raw HTTP GET web fetch."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    status_code: int | None = Field(default=None, description="HTTP response status code")
    url: str = Field(default="", description="Fetched URL")
    headers: dict[str, str] = Field(default_factory=dict, description="Response HTTP headers")
    body: str | None = Field(default=None, description="Decoded textual response body")
    error: str | None = Field(default=None, description="Error explanation if fetch failed")


class WebMarkdownResult(BaseModel):
    """Result of fetching a URL and distilling HTML to clean Markdown."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    url: str = Field(default="", description="Fetched URL")
    markdown: str = Field(default="", description="Cleaned, structured Markdown distillation")
    length_chars: int = Field(default=0, description="Character length of Markdown output")
    error: str | None = Field(default=None, description="Error explanation if fetch/distill failed")


class WebHttpResponse(BaseModel):
    """Result of custom HTTP request execution."""

    status: str = Field(default="ok", description="Status indicator (ok, error)")
    status_code: int | None = Field(default=None, description="HTTP status code")
    url: str = Field(default="", description="Target request URL")
    headers: dict[str, str] = Field(default_factory=dict, description="Response headers")
    json_data: Any | None = Field(default=None, description="Parsed JSON response payload if applicable")
    body: str | None = Field(default=None, description="Raw text response body if not JSON")
    error: str | None = Field(default=None, description="Error explanation if request failed")


@runtime_checkable
class WebFetcherService(Protocol):
    """Protocol for web fetching, HTML distillation, and HTTP client requests."""

    def fetch_url(self, url: str, timeout: float = 15.0) -> WebFetchResult:
        """Fetch URL synchronously."""
        ...

    async def fetch_url_async(self, url: str, timeout: float = 15.0) -> WebFetchResult:
        """Fetch URL asynchronously without blocking event loops."""
        ...

    def fetch_markdown(self, url: str, timeout: float = 15.0) -> WebMarkdownResult:
        """Fetch URL and distill to clean Markdown synchronously."""
        ...

    async def fetch_markdown_async(self, url: str, timeout: float = 15.0) -> WebMarkdownResult:
        """Fetch URL and distill to clean Markdown asynchronously."""
        ...

    def http_request(
        self,
        url: str,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        json_data: dict[str, Any] | None = None,
        timeout: float = 15.0,
    ) -> WebHttpResponse:
        """Execute custom HTTP request synchronously."""
        ...

    async def http_request_async(
        self,
        url: str,
        method: str = "GET",
        headers: dict[str, str] | None = None,
        json_data: dict[str, Any] | None = None,
        timeout: float = 15.0,
    ) -> WebHttpResponse:
        """Execute custom HTTP request asynchronously."""
        ...


WEB_FETCHER_KEY: ServiceKey[WebFetcherService] = ServiceKey("service.web_fetcher")
