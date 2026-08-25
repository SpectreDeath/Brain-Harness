"""Tests for Stagehand Browser Plugin and Kernel Service Integration."""

import pytest

from harness.kernel.context import ServiceContext
from harness.services.stagehand_browser import (
    STAGEHAND_BROWSER_KEY,
    StagehandActResult,
    StagehandBrowserService,
    StagehandExtractResult,
    StagehandObserveResult,
    StagehandSessionStatus,
    StagehandWebMCPResult,
)
from plugins.integration_and_io.stagehand_browser import (
    StagehandBrowserEngine,
    StagehandBrowserPlugin,
)
from plugins.integration_and_io.stagehand_browser.main import (
    stagehand_act,
    stagehand_extract,
    stagehand_observe,
    stagehand_session_control,
    stagehand_webmcp_tool_invoke,
)


@pytest.mark.unit
def test_stagehand_act_and_variables():
    """Test natural language action execution and variable interpolation."""
    engine = StagehandBrowserEngine()

    # Direct act
    res1 = engine.act(action="click button#submit", timeout_s=15)
    assert res1["status"] == "ok"
    assert res1["success"] is True
    assert "clicked" in res1["message"].lower()

    # Act with template variables
    res2 = engine.act(
        action="type {search_term} into input[name='q']",
        variables={"search_term": "Browserbase Stagehand"},
    )
    assert res2["status"] == "ok"
    assert "Browserbase Stagehand" in res2["action_performed"]


@pytest.mark.unit
def test_stagehand_extract_schema():
    """Test structured data extraction with JSON schema."""
    engine = StagehandBrowserEngine()

    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "price": {"type": "number"},
            "in_stock": {"type": "boolean"},
            "tags": {"type": "array"},
        },
        "required": ["title", "price"],
    }

    res = engine.extract(instruction="Extract product card data", schema=schema)
    assert res["status"] == "ok"
    assert "data" in res
    assert "title" in res["data"]
    assert "price" in res["data"]
    assert isinstance(res["data"]["price"], (int, float))
    assert res["data"]["in_stock"] is True


@pytest.mark.unit
def test_stagehand_observe_elements():
    """Test live DOM observation and interactive element suggestions."""
    engine = StagehandBrowserEngine()

    res = engine.observe(instruction="search", return_action=True)
    assert res["status"] == "ok"
    assert len(res["elements"]) >= 1
    first_el = res["elements"][0]
    assert "selector" in first_el
    assert "description" in first_el
    assert "action_suggested" in first_el


@pytest.mark.unit
def test_stagehand_webmcp_discovery_and_invocation():
    """Test WebMCP tool discovery and invocation."""
    engine = StagehandBrowserEngine()

    # 1. Enumerate available WebMCP tools
    list_res = engine.invoke_webmcp_tool(tool_name="__list__")
    assert list_res["status"] == "ok"
    assert len(list_res["available_tools"]) >= 2
    tool_names = [t["name"] for t in list_res["available_tools"]]
    assert "get_product_details" in tool_names

    # 2. Invoke valid tool
    inv_res = engine.invoke_webmcp_tool(
        tool_name="get_product_details",
        arguments={"product_id": "SKU_998"},
    )
    assert inv_res["status"] == "ok"
    assert inv_res["invocation_status"] == "Completed"
    assert inv_res["output"]["tool"] == "get_product_details"

    # 3. Invoke non-existent tool
    err_res = engine.invoke_webmcp_tool(tool_name="non_existent_tool")
    assert err_res["status"] == "error"
    assert err_res["error_text"] is not None


@pytest.mark.unit
def test_stagehand_session_control_lifecycle():
    """Test browser session init, goto, screenshot, evaluate, and close."""
    engine = StagehandBrowserEngine()

    # Init
    init_res = engine.control_session(action="init", url="https://example.com")
    assert init_res["status"] == "ok"
    assert init_res["current_url"] == "https://example.com"

    # Goto
    goto_res = engine.control_session(action="goto", url="https://github.com")
    assert goto_res["status"] == "ok"
    assert goto_res["current_url"] == "https://github.com"

    # Screenshot
    shot_res = engine.control_session(action="screenshot")
    assert shot_res["status"] == "ok"
    assert shot_res["screenshot_b64"] is not None

    # Evaluate
    eval_res = engine.control_session(action="evaluate", script="document.title")
    assert eval_res["status"] == "ok"
    assert eval_res["eval_result"] is not None

    # Close
    close_res = engine.control_session(action="close")
    assert close_res["status"] == "closed"


@pytest.mark.asyncio
async def test_stagehand_plugin_service_integration():
    """Test StagehandBrowserPlugin service registration and IoC context resolution."""
    plugin = StagehandBrowserPlugin()
    ctx = ServiceContext()

    assert STAGEHAND_BROWSER_KEY in plugin.provides

    await plugin.on_load(ctx)
    await plugin.on_enable()

    service = ctx.require(STAGEHAND_BROWSER_KEY)
    assert service is not None

    act_res = await service.act(action="click #login-btn")
    assert isinstance(act_res, StagehandActResult)
    assert act_res.status == "ok"
    assert act_res.success is True

    obs_res = await service.observe()
    assert isinstance(obs_res, StagehandObserveResult)
    assert len(obs_res.elements) >= 1

    await plugin.on_disable()
    await plugin.on_unload()
