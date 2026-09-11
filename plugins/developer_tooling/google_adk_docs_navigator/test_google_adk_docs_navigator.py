"""Tests for Google ADK Docs Navigator Plugin."""

import pytest
from harness.kernel.context import ServiceContext
from plugins.developer_tooling.google_adk_docs_navigator.main import (
    GOOGLE_ADK_DOCS_NAVIGATOR_SERVICE_KEY,
    GoogleAdkDocsNavigatorPlugin,
)

@pytest.mark.asyncio
async def test_google_adk_docs_navigator_tools():
    ctx = ServiceContext()
    p = GoogleAdkDocsNavigatorPlugin()
    await p.enable(ctx)

    service = ctx.require(GOOGLE_ADK_DOCS_NAVIGATOR_SERVICE_KEY)
    assert service is not None

    # Test docs search
    res = service.docs_search("agent", limit=2)
    assert res["status"] == "success"
    assert len(res["results"]) > 0

    # Test API reference
    api_res = service.get_api_reference("Agent", "python")
    assert api_res["status"] == "success"
    assert "class Agent" in api_res["signature"]

    # Test llms.txt fetch
    llms_res = service.fetch_llms_txt()
    assert llms_res["status"] == "success"
    assert len(llms_res["content_snippet"]) > 0

    await p.disable(ctx)
