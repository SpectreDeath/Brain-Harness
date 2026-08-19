"""Tests for HarnessRuntime — unified kernel orchestrator."""

from __future__ import annotations

from typing import Any

import pytest

from harness.events.types import HarnessEvent
from harness.kernel.context import ServiceKey
from harness.kernel.runtime import HarnessRuntime
from harness.plugins.base import HarnessPlugin
from harness.services.llm import LiteLLMService, LLMResponse
from harness.services.tools import TOOL_REGISTRY_KEY


class DummyCustomPlugin(HarnessPlugin):
    @property
    def name(self) -> str:
        return "test.dummy"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [ServiceKey("test.dummy_service")]

    async def on_load(self, ctx: Any) -> None:
        ctx.provide(self.provides[0], "dummy_value", provider=self.name)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_runtime_context_manager() -> None:
    """Verify async context manager startup and shutdown lifecycle."""
    events_received: list[HarnessEvent] = []

    async def on_event(event: HarnessEvent) -> None:
        events_received.append(event)

    async with HarnessRuntime.create(db_path=":memory:") as runtime:
        runtime.event_bus.on_all(on_event)
        assert runtime.is_running is True
        assert runtime.context is not None
        assert runtime.lifecycle is not None
        assert runtime.tools is not None

        # Verify built-in services
        assert runtime.context.has(TOOL_REGISTRY_KEY)
        summary = runtime.summary()
        assert "tools.registry" in summary
        assert summary["tools.registry"] == "enabled"

    # Verify stopped
    assert runtime.is_running is False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_runtime_custom_plugin_registration() -> None:
    """Verify registering and resolving custom plugins through runtime."""
    runtime = HarnessRuntime.create(db_path=":memory:")
    runtime.register_plugin(DummyCustomPlugin())

    await runtime.start()
    try:
        assert runtime.context.has(ServiceKey("test.dummy_service"))
        assert runtime.require(ServiceKey("test.dummy_service")) == "dummy_value"
    finally:
        await runtime.stop()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_runtime_agent_run_task() -> None:
    """Verify running tasks via runtime.run_task()."""
    class MockLLM(LiteLLMService):
        async def complete(self, messages: Any, **kwargs: Any) -> Any:
            return LLMResponse(content="FINAL ANSWER: Runtime test passed.")

    async with HarnessRuntime.create(db_path=":memory:", llm=MockLLM()) as runtime:
        result = await runtime.run_task("Test task")
        assert result.status == "completed"
        assert result.final_answer == "Runtime test passed."


@pytest.mark.integration
@pytest.mark.asyncio
async def test_runtime_plugin_and_tool_enablement() -> None:
    """Verify runtime enable/disable methods for plugins and tools."""
    async with HarnessRuntime.create(db_path=":memory:") as runtime:
        # Disable Em-Cubed bridge plugin
        assert await runtime.disable_plugin("bridge.em_cubed") is True
        summary = runtime.summary()
        assert summary["bridge.em_cubed"] == "disabled"

        # Re-enable Em-Cubed
        assert await runtime.enable_plugin("bridge.em_cubed") is True
        summary = runtime.summary()
        assert summary["bridge.em_cubed"] == "enabled"

        # Test granular tool enablement
        all_tools = runtime.tools.list_tools()
        assert len(all_tools) > 0
        first_tool_name = all_tools[0].name

        assert runtime.disable_tool(first_tool_name) is True
        assert runtime.tools.is_tool_enabled(first_tool_name) is False

        assert runtime.enable_tool(first_tool_name) is True
        assert runtime.tools.is_tool_enabled(first_tool_name) is True

        assert runtime.toggle_tool(first_tool_name) is True
        assert runtime.tools.is_tool_enabled(first_tool_name) is False

        # Bulk disable
        disabled = await runtime.disable_all_plugins(keep_core=True)
        assert len(disabled) > 0
        # Core plugins should remain enabled
        assert runtime.lifecycle.get_state("tools.registry").value == "enabled"
        assert runtime.lifecycle.get_state("storage.sqlite").value == "enabled"

        # Bulk enable
        results = await runtime.enable_all_plugins()
        assert sum(results.values()) > 0
