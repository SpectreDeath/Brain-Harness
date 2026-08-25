"""Unit tests for the OpenRouter Gateway plugin (plugin.openrouter_gateway)."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from plugins.integration_and_io.openrouter_gateway.headers import (
    HEADER_EDITOR_NAME,
    HEADER_FEATURE,
    HEADER_ORGANIZATION_ID,
    HEADER_TASK_ID,
    HEADER_TESTER,
    TESTER_SUPPRESS_VALUE,
    build_kilo_headers,
)
from plugins.integration_and_io.openrouter_gateway.main import (
    OpenRouterGatewayPlugin,
    openrouter_jsonrpc_call,
    openrouter_resolve_route,
)
from harness.services.openrouter_gateway import (
    OPENROUTER_GATEWAY_KEY,
    OpenRouterGatewayService,
    RouteResolution,
)


@pytest.mark.unit
def test_manifest_validation() -> None:
    """Validate that the plugin passes all PluginValidator rules."""
    plugin_dir = Path("plugins/integration_and_io/openrouter_gateway").resolve()
    report = PluginValidator.validate_sync(plugin_dir)
    assert report.valid, f"Validation failed with errors: {report.errors}"
    assert len(report.errors) == 0


@pytest.mark.unit
def test_headers_construction() -> None:
    """Verify metadata and attribution header generation."""
    headers = build_kilo_headers(
        task_id="task-999",
        organization_id="org-kilo-1",
        feature="subagent_task",
        tester_warnings_disabled_until=time.time() + 1000,
        machine_id="mach-01",
    )

    assert headers[HEADER_TASK_ID] == "task-999"
    assert headers[HEADER_ORGANIZATION_ID] == "org-kilo-1"
    assert headers[HEADER_FEATURE] == "subagent_task"
    assert headers[HEADER_TESTER] == TESTER_SUPPRESS_VALUE
    assert "Brain Harness" in headers[HEADER_EDITOR_NAME]
    assert headers["HTTP-Referer"] == "https://github.com/SpectreDeath/Brain-Harness"


@pytest.mark.unit
def test_context_epoch_formatting() -> None:
    """Verify Context Epoch prompt formatting (KI-KILO-01)."""
    service = OpenRouterGatewayService()
    baseline = "You are a helpful coding assistant."
    messages = [
        {"role": "user", "content": "Refactor this function"},
        {"role": "assistant", "content": "Here is the refactored function..."},
    ]
    updates = [
        "File edited: src/core.py (2 lines changed)",
        "Linter error resolved in test_core.py",
    ]

    formatted = service.format_context_epoch(baseline, messages, mid_conversation_updates=updates)

    assert len(formatted) == 4
    assert formatted[0] == {"role": "system", "content": baseline}
    assert formatted[1] == messages[0]
    assert formatted[2] == messages[1]
    assert formatted[3]["role"] == "system"
    assert "[Context Update]" in formatted[3]["content"]
    assert "File edited: src/core.py" in formatted[3]["content"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_route_resolution() -> None:
    """Verify intelligent route selection based on task type and complexity."""
    service = OpenRouterGatewayService()

    # 1. Reasoning task
    route_reasoning = await service.resolve_route("Deep architecture reasoning", tier="high")
    assert "claude-3.7-sonnet" in route_reasoning.selected_model
    assert route_reasoning.reasoning_budget == "high"

    # 2. Code editing task
    route_code = await service.resolve_route("code refactoring and edit")
    assert "claude-3.7-sonnet" in route_code.selected_model
    assert route_code.reasoning_budget == "medium"

    # 3. Fast summary task
    route_summary = await service.resolve_route("quick summary", budget="low")
    assert "gemini" in route_summary.selected_model or "llama" in route_summary.selected_model
    assert route_summary.reasoning_budget == "off"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_jsonrpc_dispatcher() -> None:
    """Verify JSON-RPC 2.0 protocol request parsing, execution, and error handling."""
    service = OpenRouterGatewayService()

    # Valid route request
    req = {
        "jsonrpc": "2.0",
        "method": "openrouter.route",
        "params": {"task_type": "complex architecture review", "tier": "high"},
        "id": 42,
    }
    resp = await service.jsonrpc_dispatch(req)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 42
    assert resp["error"] is None
    assert "selected_model" in resp["result"]

    # Invalid method (-32601)
    req_bad_method = {
        "jsonrpc": "2.0",
        "method": "unknown.method",
        "params": {},
        "id": "err-1",
    }
    resp_err = await service.jsonrpc_dispatch(req_bad_method)
    assert resp_err["id"] == "err-1"
    assert resp_err["error"]["code"] == -32601

    # Invalid JSON-RPC version (-32600)
    req_bad_ver = {
        "jsonrpc": "1.0",
        "method": "openrouter.route",
        "params": {},
        "id": "err-2",
    }
    resp_bad_ver = await service.jsonrpc_dispatch(req_bad_ver)
    assert resp_bad_ver["error"]["code"] == -32600

    # Batch request
    batch_req = [req, req_bad_method]
    batch_resp = await service.jsonrpc_dispatch(batch_req)
    assert "batch" in batch_resp
    assert len(batch_resp["batch"]) == 2
    assert batch_resp["batch"][0]["id"] == 42
    assert batch_resp["batch"][1]["id"] == "err-1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mocked_chat_completion() -> None:
    """Verify chat completion handling and choice parsing with mocked HTTP transport."""
    service = OpenRouterGatewayService(api_key="test-key")

    mock_response = {
        "id": "gen-12345",
        "model": "anthropic/claude-3.7-sonnet",
        "choices": [
            {
                "message": {"role": "assistant", "content": "Synthesized code response."},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 150, "completion_tokens": 45, "total_tokens": 195},
    }

    with patch.object(service, "_async_http_post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        res = await service.chat(
            messages=[{"role": "user", "content": "Hello"}],
            model="anthropic/claude-3.7-sonnet",
            reasoning={"effort": "high"},
            order=["Anthropic", "Together"],
            task_id="task-100",
        )

        assert res.id == "gen-12345"
        assert res.content == "Synthesized code response."
        assert res.usage["total_tokens"] == 195
        mock_post.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_plugin_ioc_lifecycle() -> None:
    """Verify plugin loading, IoC context registration, and tool entrypoints."""
    plugin = OpenRouterGatewayPlugin()
    assert plugin.name == "plugin.openrouter_gateway"
    assert plugin.provides == [OPENROUTER_GATEWAY_KEY]

    ctx = ServiceContext()
    await plugin.on_load(ctx)

    # Verify service is resolvable via typed key
    resolved = ctx.require(OPENROUTER_GATEWAY_KEY)
    assert isinstance(resolved, OpenRouterGatewayService)

    # Test top-level tool exports
    route_tool_res = openrouter_resolve_route("reasoning task", tier="high")
    assert route_tool_res["status"] == "ok"
    assert "route" in route_tool_res

    rpc_tool_res = openrouter_jsonrpc_call({
        "jsonrpc": "2.0",
        "method": "openrouter.route",
        "params": {"task_type": "coding"},
        "id": "test-rpc",
    })
    assert rpc_tool_res["status"] == "ok"
    assert rpc_tool_res["jsonrpc_response"]["id"] == "test-rpc"
