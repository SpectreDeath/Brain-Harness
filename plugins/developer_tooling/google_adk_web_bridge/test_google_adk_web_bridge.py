"""Tests for Google ADK Web Bridge Plugin."""

import pytest
from harness.kernel.context import ServiceContext
from plugins.developer_tooling.google_adk_web_bridge.main import (
    GOOGLE_ADK_WEB_BRIDGE_SERVICE_KEY,
    GoogleAdkWebBridgePlugin,
)

@pytest.mark.asyncio
async def test_google_adk_web_bridge_tools():
    ctx = ServiceContext()
    p = GoogleAdkWebBridgePlugin()
    await p.enable(ctx)

    service = ctx.require(GOOGLE_ADK_WEB_BRIDGE_SERVICE_KEY)
    assert service is not None

    # Test web status
    status = service.web_status()
    assert status["status"] == "success"

    # Test graph export to A2UI
    nodes = [{"id": "n1", "label": "Planner"}, {"id": "n2", "label": "Executor"}]
    edges = [{"source": "n1", "target": "n2"}]
    export = service.export_graph(nodes, edges, format="a2ui")
    assert export["status"] == "success"
    assert export["node_count"] == 2

    # Test graph export to Mermaid
    m_export = service.export_graph(nodes, edges, format="mermaid")
    assert "graph TD" in m_export["graph_data"]

    # Test start dev server config
    dev = service.start_dev_server(port=5000)
    assert dev["status"] == "success"
    assert dev["port"] == 5000

    await p.disable(ctx)
