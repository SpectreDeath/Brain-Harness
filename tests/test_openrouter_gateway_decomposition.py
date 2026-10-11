"""Contract verification test suite for OpenRouter Gateway service decomposition.

Verifies:
1. Architectural bounds: all submodules <= 200 lines (Rule 11).
2. Protocol conformance & single-seam IoC resolution (Rule 2, Rule 49, Rule 58).
3. Header construction and Context Epoch KV-cache preservation.
4. Backward-compatible facade re-exports and routing heuristics.
5. Plugin module singleton export (Rule 45).
"""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext, ServiceKey
from harness.services.openrouter_gateway import (
    DEFAULT_EDITOR_NAME,
    DEFAULT_OPENROUTER_BASE_URL,
    HEADER_EDITOR_NAME,
    JSONRPCError,
    JSONRPCResponse,
    ModelMessage,
    OPENROUTER_GATEWAY_KEY,
    OpenRouterChatResponse,
    OpenRouterGatewayService,
    OpenRouterGatewayServiceProtocol,
    OpenRouterModelInfo,
    ProviderPreferences,
    ReasoningConfig,
    RouteResolution,
    build_kilo_headers,
    execute_chat_completion,
    execute_jsonrpc_dispatch,
    execute_jsonrpc_single,
    format_context_epoch_messages,
    resolve_model_route,
    resolve_openrouter_gateway_service,
)


class TestOpenRouterGatewayDecomposition:
    """Contract tests verifying the architectural invariants of OpenRouter Gateway decomposition."""

    def test_submodule_line_bounds(self) -> None:
        """Verify all submodules in src/harness/services/openrouter_gateway/ are <= 200 lines per Rule 11."""
        gateway_dir = Path(__file__).parent.parent / "src" / "harness" / "services" / "openrouter_gateway"
        assert gateway_dir.is_dir(), f"Expected directory at {gateway_dir}"

        py_files = list(gateway_dir.glob("*.py"))
        assert len(py_files) >= 9, f"Expected at least 9 submodules, found {len(py_files)}"

        for py_file in py_files:
            line_count = len(py_file.read_text(encoding="utf-8").splitlines())
            assert (
                line_count <= 200
            ), f"{py_file.name} has {line_count} lines, exceeding the 200-line limit (Rule 11)"

    def test_protocol_conformance_and_single_seam_resolver(self) -> None:
        """Verify protocol conformance and single-seam IoC resolution per Rule 49 & 58."""
        service = OpenRouterGatewayService()
        assert isinstance(service, OpenRouterGatewayServiceProtocol)
        assert isinstance(OPENROUTER_GATEWAY_KEY, ServiceKey)
        assert OPENROUTER_GATEWAY_KEY.name == "service.openrouter_gateway"

        # Fallback resolution with no context
        resolved_default = resolve_openrouter_gateway_service(None)
        assert isinstance(resolved_default, OpenRouterGatewayServiceProtocol)

        # Context-based resolution
        ctx = ServiceContext()
        custom_service = OpenRouterGatewayService(api_key="custom_test_key")
        ctx.provide(OPENROUTER_GATEWAY_KEY, custom_service)

        resolved_ctx = resolve_openrouter_gateway_service(ctx)
        assert resolved_ctx is custom_service

    def test_headers_and_context_epoch_formatting(self) -> None:
        """Verify Kilo attribution headers and Context Epoch message ordering."""
        headers = build_kilo_headers(task_id="task-123", feature="test-feat")
        assert headers["Content-Type"] == "application/json"
        assert headers[HEADER_EDITOR_NAME] == DEFAULT_EDITOR_NAME
        assert headers["X-KiloCode-TaskId"] == "task-123"
        assert headers["X-KiloCode-Feature"] == "test-feat"

        msgs = format_context_epoch_messages(
            baseline_system_prompt="System baseline",
            messages=[{"role": "user", "content": "Hello"}],
            mid_conversation_updates=["Env changed"],
        )
        assert len(msgs) == 3
        assert msgs[0]["role"] == "system"
        assert msgs[0]["content"] == "System baseline"
        assert msgs[1]["content"] == "Hello"
        assert "[Context Update]" in msgs[2]["content"]

    def test_routing_heuristics(self) -> None:
        """Verify intelligent route selection based on task complexity."""
        route_arch = resolve_model_route("Complex architectural refactoring", tier="high")
        assert "claude-3.7-sonnet" in route_arch.selected_model
        assert route_arch.reasoning_budget == "high"

        route_fast = resolve_model_route("quick summary", tier="low", budget="low")
        assert "gemini-2.0-flash" in route_fast.selected_model
        assert route_fast.reasoning_budget == "off"

    def test_plugin_module_singleton_export(self) -> None:
        """Verify plugin module-level singleton export per Rule 45."""
        from plugins.integration_and_io.openrouter_gateway.main import (
            OpenRouterGatewayPlugin,
            plugin,
        )

        assert isinstance(plugin, OpenRouterGatewayPlugin)
        assert OPENROUTER_GATEWAY_KEY in plugin.provides
        assert plugin.name == "plugin.openrouter_gateway"
