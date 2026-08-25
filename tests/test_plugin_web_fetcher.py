"""Tests for web_fetcher plugin."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from harness.kernel.context import ServiceContext
from harness.services.web_fetcher import (
    WEB_FETCHER_KEY,
    WebFetcherService,
    WebFetchResult,
    WebHttpResponse,
    WebMarkdownResult,
)
from plugins.integration_and_io.web_fetcher.main import (
    WebFetcherPlugin,
    _html_to_markdown,
    web_fetch_markdown,
    web_fetch_url,
    web_http_request,
)


@pytest.mark.unit
class TestWebFetcherPlugin:
    def test_html_to_markdown_conversion(self) -> None:
        html = """
        <html>
          <head><title>Test</title><script>var x = 1;</script></head>
          <body>
            <h1>Main Title</h1>
            <p>Here is a paragraph with <a href="https://example.com">a link</a> and <code>code snippet</code>.</p>
            <ul>
              <li>Item 1</li>
              <li>Item 2</li>
            </ul>
            <pre><code>def hello(): pass</code></pre>
          </body>
        </html>
        """
        md = _html_to_markdown(html)
        assert "# Main Title" in md
        assert "[a link](https://example.com)" in md
        assert "`code snippet`" in md
        assert "- Item 1" in md
        assert "var x = 1;" not in md  # Script stripped

    def test_web_fetch_url_mocked(self) -> None:
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.info.return_value.get_content_charset.return_value = "utf-8"
        mock_response.info.return_value.__iter__.return_value = [("content-type", "text/html")]
        mock_response.read.return_value = b"<h1>Example Domain</h1>"

        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_response

            res = web_fetch_url("https://example.com")
            assert res["status"] == "ok"
            assert res["status_code"] == 200
            assert "Example Domain" in res["body"]

            res_md = web_fetch_markdown("https://example.com")
            assert res_md["status"] == "ok"
            assert "# Example Domain" in res_md["markdown"]

    def test_web_http_request_json(self) -> None:
        mock_response = MagicMock()
        mock_response.getcode.return_value = 201
        mock_response.info.return_value = {"Content-Type": "application/json"}
        mock_response.read.return_value = b'{"created": true, "id": 123}'

        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_response

            res = web_http_request(
                "https://api.example.com/items",
                method="POST",
                json_data={"name": "test"},
            )
            assert res["status"] == "ok"
            assert res["status_code"] == 201
            assert res["json"] == {"created": True, "id": 123}

    @pytest.mark.asyncio
    async def test_plugin_ioc_lifecycle_and_async_fetch(self) -> None:
        plugin = WebFetcherPlugin()
        assert plugin.name == "plugin.web_fetcher"
        assert WEB_FETCHER_KEY in plugin.provides

        ctx = ServiceContext()
        await plugin.on_load(ctx)
        await plugin.on_enable()

        service = ctx.require(WEB_FETCHER_KEY)
        assert isinstance(service, WebFetcherService)

        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.info.return_value.get_content_charset.return_value = "utf-8"
        mock_response.info.return_value.__iter__.return_value = [("content-type", "text/html")]
        mock_response.read.return_value = b"<h2>Async Title</h2>"

        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_response

            async_fetch_res = await service.fetch_url_async("https://async.example.com")
            assert isinstance(async_fetch_res, WebFetchResult)
            assert async_fetch_res.status == "ok"
            assert "Async Title" in (async_fetch_res.body or "")

            async_md_res = await service.fetch_markdown_async("https://async.example.com")
            assert isinstance(async_md_res, WebMarkdownResult)
            assert "## Async Title" in async_md_res.markdown

        mock_json_resp = MagicMock()
        mock_json_resp.getcode.return_value = 200
        mock_json_resp.info.return_value = {"Content-Type": "application/json"}
        mock_json_resp.read.return_value = b'{"success": true}'

        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_json_resp

            http_res = await service.http_request_async(
                "https://api.async.com", method="GET"
            )
            assert isinstance(http_res, WebHttpResponse)
            assert http_res.json_data == {"success": True}

        await plugin.on_disable()
        await plugin.on_unload()
