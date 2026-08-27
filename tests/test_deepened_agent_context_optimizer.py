"""Tests for AgentContextOptimizer seam, DefaultContextOptimizer, and StepExecutionEngine integration."""

import asyncio
import pytest

from harness.agent.context_optimizer import (
    AGENT_CONTEXT_OPTIMIZER_KEY,
    AgentContextOptimizer,
    ContextOptimizationConfig,
    DefaultContextOptimizer,
)
from harness.agent.react import (
    ReActAgentLoop,
    ReActAgentPlugin,
    StepExecutionEngine,
)
from harness.agent.base import AgentTrajectory
from harness.kernel.context import ServiceContext
from harness.services.llm import LLMMessage, LLMResponse, LLMService, LLM_SERVICE_KEY
from harness.services.tools import ToolRegistry, TOOL_REGISTRY_KEY, ToolSpec


class MockLLM(LLMService):
    def __init__(self, responses: list[LLMResponse] | None = None) -> None:
        self.responses = list(responses or [])
        self.call_count = 0
        self.last_messages: list[LLMMessage] = []

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        self.call_count += 1
        self.last_messages = list(messages)
        if self.responses:
            return self.responses.pop(0)
        return LLMResponse(content="FINAL ANSWER: Task completed successfully")

    async def stream(
        self,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ):
        yield "FINAL ANSWER: Task completed successfully"


@pytest.mark.asyncio
async def test_default_context_optimizer_compaction():
    opt = DefaultContextOptimizer(ContextOptimizationConfig(max_observation_chars=100))

    # Test small string
    res = opt.compact_observation("test", "small observation")
    assert res == "small observation"

    # Test huge string truncation
    huge_str = "A" * 500
    res = opt.compact_observation("test", huge_str)
    assert "[TRUNCATED 400 CHARS]" in res

    # Test JSON compaction
    dict_val = {"key": "value", "list": [1, 2, 3]}
    res = opt.compact_observation("test", dict_val)
    assert '{"key":"value","list":[1,2,3]}' == res

    # Test huge JSON truncation
    huge_dict = {"data": "X" * 300}
    res = opt.compact_observation("test", huge_dict)
    assert "[TRUNCATED JSON" in res


@pytest.mark.asyncio
async def test_default_context_optimizer_windowing():
    opt = DefaultContextOptimizer(
        ContextOptimizationConfig(
            max_total_messages=6,
            recent_messages_preserve=2,
            enable_pruning=True,
        )
    )

    # 10 messages: header (2) + intermediate (6) + tail (2)
    messages = [
        LLMMessage(role="system", content="System instruction"),
        LLMMessage(role="user", content="Task: solve math problem"),
        LLMMessage(role="assistant", content="Step 1 thought"),
        LLMMessage(role="user", content="Step 1 obs"),
        LLMMessage(role="assistant", content="Step 2 thought"),
        LLMMessage(role="user", content="Step 2 obs"),
        LLMMessage(role="assistant", content="Step 3 thought"),
        LLMMessage(role="user", content="Step 3 obs"),
        LLMMessage(role="assistant", content="Step 4 thought"),
        LLMMessage(role="user", content="Step 4 obs"),
    ]

    pruned = opt.optimize_messages(messages)
    assert len(pruned) < len(messages)
    assert pruned[0].content == "System instruction"
    assert pruned[1].content == "Task: solve math problem"
    assert "[CONTEXT PRUNING:" in pruned[2].content
    assert pruned[-1].content == "Step 4 obs"


@pytest.mark.asyncio
async def test_step_execution_engine_with_optimizer():
    llm = MockLLM(
        responses=[
            LLMResponse(
                content="Calling tool",
                tool_calls=[{"id": "tc1", "name": "echo_big", "arguments": {"text": "hello"}}],
            ),
            LLMResponse(content="FINAL ANSWER: Done with big output"),
        ]
    )
    tools = ToolRegistry()

    def echo_big(text: str) -> dict:
        return {"result": text + ("_long" * 100)}

    tools.register(ToolSpec.from_callable(echo_big, name="echo_big"))

    optimizer = DefaultContextOptimizer(ContextOptimizationConfig(max_observation_chars=120))
    engine = StepExecutionEngine(llm=llm, tools=tools, optimizer=optimizer)

    traj = AgentTrajectory(task="Test big output compaction")
    traj.messages = engine.build_initial_messages(traj.task)

    # Step 1: Tool call
    cont = await engine.execute_step(traj, 1)
    assert cont is True
    assert len(traj.steps) == 1
    # Check that observation was compacted in trajectory messages
    last_user_msg = traj.messages[-1]
    assert "[TRUNCATED JSON" in last_user_msg.content

    # Step 2: Final answer
    cont = await engine.execute_step(traj, 2)
    assert cont is False
    assert traj.status == "completed"
    assert traj.final_answer == "Done with big output"


@pytest.mark.asyncio
async def test_react_agent_plugin_provides_optimizer_integration():
    ctx = ServiceContext()

    llm = MockLLM()
    tools = ToolRegistry()
    ctx.provide(LLM_SERVICE_KEY, llm)
    ctx.provide(TOOL_REGISTRY_KEY, tools)

    custom_opt = DefaultContextOptimizer(ContextOptimizationConfig(max_observation_chars=80))
    ctx.provide(AGENT_CONTEXT_OPTIMIZER_KEY, custom_opt)

    plugin = ReActAgentPlugin()
    await plugin.on_load(ctx)
    await plugin.on_enable()

    assert plugin._loop is not None
    assert plugin._loop.step_engine.optimizer is custom_opt

    await plugin.on_disable()
    await plugin.on_unload()
