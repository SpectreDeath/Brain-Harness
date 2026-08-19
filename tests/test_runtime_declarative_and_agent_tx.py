"""Tests for Declarative Runtime Initialization and Transactional ReAct Step Sandboxing.

Verifies:
1. HarnessRuntime.from_config() factory and automatic start reconciliation.
2. Live runtime.reconcile() dynamic hot-configuration.
3. ReAct StepExecutionEngine transactional rollback on tool execution errors.
4. CLI apply and config validate commands.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from click.testing import CliRunner

from harness.agent.base import AgentTrajectory
from harness.agent.react import ReActAgentLoop, StepExecutionEngine
from harness.cli import main
from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.lifecycle import PluginState
from harness.kernel.reconciler import HarnessConfigTree, PluginConfigEntry
from harness.kernel.runtime import HarnessRuntime
from harness.plugins.base import HarnessPlugin
from harness.services.llm import LLMMessage, LLMResponse, LLMService
from harness.services.tools import ToolRegistry, ToolSpec


class MockPluginA(HarnessPlugin):
    name = "plugin.a"
    version = "1.0.0"
    provides = [ServiceKey[str]("svc.a")]

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(self.provides[0], "value_a")


class MockPluginB(HarnessPlugin):
    name = "plugin.b"
    version = "1.0.0"
    requires = [ServiceKey[str]("svc.a")]
    provides = [ServiceKey[str]("svc.b")]

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(self.provides[0], "value_b")


# --- Test Declarative Runtime ---


@pytest.mark.integration
@pytest.mark.asyncio
async def test_runtime_from_config(tmp_path: Path) -> None:
    """Test creating and starting HarnessRuntime from a declarative config file."""
    config_data = {
        "version": "1.0.0",
        "plugins": [
            {"id": "entry_a", "name": "plugin.a"},
            {"id": "entry_b", "name": "plugin.b"},
        ],
    }
    config_file = tmp_path / "harness.json"
    config_file.write_text(json.dumps(config_data), encoding="utf-8")

    runtime = HarnessRuntime.from_config(config_file)
    runtime.register_plugin(MockPluginA())
    runtime.register_plugin(MockPluginB())

    await runtime.start()

    assert runtime.lifecycle.get_state("plugin.a") == PluginState.ENABLED
    assert runtime.lifecycle.get_state("plugin.b") == PluginState.ENABLED
    assert runtime.context.require(ServiceKey[str]("svc.a")) == "value_a"
    assert runtime.context.require(ServiceKey[str]("svc.b")) == "value_b"

    # Reconcile hot-removal of plugin.b
    res = await runtime.reconcile(
        {
            "version": "1.0.0",
            "plugins": [{"id": "entry_a", "name": "plugin.a"}],
        }
    )
    assert res.is_clean
    assert "plugin.b" in res.removed
    assert runtime.lifecycle.get_state("plugin.b") == PluginState.UNLOADED
    assert not runtime.context.has(ServiceKey[str]("svc.b"))

    await runtime.stop()


# --- Test Transactional ReAct Steps ---


class MockMockLLM(LLMService):
    def __init__(self, responses: list[LLMResponse]) -> None:
        self.responses = list(responses)
        self.call_count = 0

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        resp = self.responses[self.call_count]
        self.call_count += 1
        return resp

    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        tools: list[dict[str, Any]] | None = None,
    ) -> Any:
        yield (await self.complete(messages, temperature=temperature, max_tokens=max_tokens, tools=tools)).content


@pytest.mark.unit
@pytest.mark.asyncio
async def test_react_step_transactional_rollback() -> None:
    """Test that a failing tool call within a ReAct step cleanly rolls back context mutations."""
    ctx = ServiceContext()
    tools = ToolRegistry()

    side_effects: list[str] = []

    async def flaky_tool_handler(**kwargs: Any) -> dict[str, Any]:
        # Perform an effect inside active context
        def _effect() -> Any:
            side_effects.append("applied")
            return lambda: side_effects.append("reverted")

        if engine.context:
            engine.context.effect(_effect)
        raise RuntimeError("Disk write failed: permission denied")

    tools.register(
        ToolSpec(
            name="flaky_tool",
            description="A tool that fails mid-execution",
            parameters_schema={"type": "object"},
            executor=flaky_tool_handler,
        )
    )

    llm = MockMockLLM(
        [
            LLMResponse(
                content="Calling flaky tool",
                tool_calls=[{"name": "flaky_tool", "arguments": {}}],
            ),
            LLMResponse(content="FINAL ANSWER: Handled error gracefully"),
        ]
    )

    engine = StepExecutionEngine(llm=llm, tools=tools, context=ctx)
    traj = AgentTrajectory(task="Test error handling")

    # Step 1: Flaky tool invocation fails
    should_continue = await engine.execute_step(traj, 1)
    assert should_continue is True
    # Verify side effects were reverted by transactional rollback
    assert side_effects == ["applied", "reverted"]
    assert "error" in traj.steps[0].observation

    # Step 2: Final answer
    should_continue = await engine.execute_step(traj, 2)
    assert should_continue is False
    assert traj.status == "completed"


# --- Test CLI Commands ---


@pytest.mark.unit
def test_cli_config_validate_and_apply(tmp_path: Path) -> None:
    """Test harness config validate and apply CLI commands."""
    runner = CliRunner()

    config_data = {
        "version": "1.0.0",
        "plugins": [
            {"id": "entry_1", "name": "core.test"},
        ],
    }
    valid_file = tmp_path / "valid_harness.json"
    valid_file.write_text(json.dumps(config_data), encoding="utf-8")

    # 1. Test validate
    res = runner.invoke(main, ["config", "validate", str(valid_file)])
    assert res.exit_code == 0
    assert "is valid" in res.output

    # 2. Test apply
    res_apply = runner.invoke(main, ["apply", "-f", str(valid_file)])
    assert res_apply.exit_code == 0
    assert "Declarative reconciliation applied successfully" in res_apply.output
