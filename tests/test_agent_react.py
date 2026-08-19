"""Tests for ReAct Autonomous Agent Loop."""

from typing import Any

import pytest

from harness.agent.base import AGENT_LOOP_KEY, AgentLoopService
from harness.agent.react import ReActAgentLoop, ReActAgentPlugin
from harness.kernel.context import ServiceContext
from harness.services.llm import LLM_SERVICE_KEY, LLMMessage, LLMResponse, LLMService
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry, ToolRegistryPlugin


class MockLLM(LLMService):
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.call_count = 0

    async def complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        content = self.responses[min(self.call_count, len(self.responses) - 1)]
        self.call_count += 1
        return LLMResponse(content=content)

    async def stream(self, messages: list[LLMMessage], **kwargs: Any) -> Any:
        yield "mock stream"


@pytest.mark.unit
@pytest.mark.asyncio
class TestReActAgent:
    async def test_direct_answer(self) -> None:
        llm = MockLLM(["Thinking... FINAL ANSWER: 42"])
        tools = ToolRegistry()

        loop = ReActAgentLoop(llm, tools)
        result = await loop.run_task("What is the answer?", max_steps=3)

        assert result.status == "completed"
        assert result.final_answer == "42"
        assert len(result.steps) == 1

    async def test_tool_call_and_solve(self) -> None:
        # Step 1 calls math tool, Step 2 provides final answer
        llm = MockLLM([
            'Let me add those numbers: ```json\n{"action": "math.add", "input": {"a": 2, "b": 3}}\n```',
            "Now I know the sum. FINAL ANSWER: The sum is 5",
        ])

        tools = ToolRegistry()

        async def add_fn(a: int, b: int) -> int:
            return a + b

        tools.register(
            name="math.add",
            description="Add numbers",
            executor=add_fn,
        )

        loop = ReActAgentLoop(llm, tools)
        result = await loop.run_task("Add 2 and 3", max_steps=5)

        assert result.status == "completed"
        assert result.final_answer == "The sum is 5"
        assert len(result.steps) == 2
        assert result.steps[0].action == "math.add"
        assert result.steps[0].observation == {"status": "ok", "result": 5}

    async def test_native_structured_tool_call(self) -> None:
        class StructuredMockLLM(LLMService):
            def __init__(self) -> None:
                self.calls = 0

            async def complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
                self.calls += 1
                if self.calls == 1:
                    return LLMResponse(
                        content="",
                        tool_calls=[{
                            "id": "call_123",
                            "function": {
                                "name": "math.multiply",
                                "arguments": '{"x": 6, "y": 7}',
                            },
                        }],
                    )
                return LLMResponse(content="FINAL ANSWER: 42")

            async def stream(self, messages: list[LLMMessage], **kwargs: Any) -> Any:
                yield ""

        tools = ToolRegistry()

        async def mult_fn(x: int, y: int) -> int:
            return x * y

        tools.register(
            name="math.multiply",
            description="Multiply numbers",
            executor=mult_fn,
        )

        loop = ReActAgentLoop(StructuredMockLLM(), tools)
        result = await loop.run_task("Multiply 6 and 7", max_steps=4)

        assert result.status == "completed"
        assert result.final_answer == "42"
        assert len(result.steps) == 2
        assert result.steps[0].action == "math.multiply"
        assert result.steps[0].action_input == {"x": 6, "y": 7}
        assert result.steps[0].observation == {"status": "ok", "result": 42}

    async def test_agent_trajectory_and_step_engine(self) -> None:
        from harness.agent.react import StepExecutionEngine

        llm = MockLLM(["Thinking about the plan... FINAL ANSWER: Trajectory success"])
        tools = ToolRegistry()

        step_engine = StepExecutionEngine(llm, tools)
        loop = ReActAgentLoop(llm, tools, step_engine=step_engine)

        trajectory = loop.create_trajectory("Inspect trajectory flow", context={"trace_id": "123"})
        assert trajectory.task == "Inspect trajectory flow"
        assert trajectory.metadata["trace_id"] == "123"
        assert len(trajectory.messages) == 2

        # Step 1 execution
        cont = await loop.step(trajectory, 1)
        assert cont is False
        assert trajectory.status == "completed"
        assert trajectory.final_answer == "Trajectory success"
        assert len(trajectory.steps) == 1

        result = trajectory.to_result()
        assert result.status == "completed"
        assert result.final_answer == "Trajectory success"
        assert result.metadata["trace_id"] == "123"

    async def test_agent_plugin_lifecycle(self) -> None:
        ctx = ServiceContext()
        tools_plugin = ToolRegistryPlugin()
        await tools_plugin.on_load(ctx)

        ctx.provide(LLM_SERVICE_KEY, MockLLM(["FINAL ANSWER: Done"]))

        plugin = ReActAgentPlugin()
        assert plugin.provides == [AGENT_LOOP_KEY]
        assert plugin.requires == [LLM_SERVICE_KEY, TOOL_REGISTRY_KEY]

        await plugin.on_load(ctx)
        await plugin.on_enable()

        assert ctx.has(AGENT_LOOP_KEY)
        loop_service: AgentLoopService = ctx.require(AGENT_LOOP_KEY)
        res = await loop_service.run_task("Test task")
        assert res.status == "completed"

        await plugin.on_disable()
        assert not ctx.has(AGENT_LOOP_KEY)

        await plugin.on_unload()
