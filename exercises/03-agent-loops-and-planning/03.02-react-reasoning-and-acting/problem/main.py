"""Exercise 03.02: ReAct Reasoning and Acting Loop (Problem)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from harness.agent.base import AgentTaskResult
from harness.services.llm import LLMMessage, LLMResponse, LLMService
from harness.services.tools import ToolRegistry


class MockLLM(LLMService):
    def __init__(self) -> None:
        self.call_count = 0

    @property
    def model_name(self) -> str:
        return "mock-model"

    async def complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
        self.call_count += 1
        if self.call_count == 1:
            return LLMResponse(content='I need to add 5 and 7.\n```json\n{"action": "math.add", "input": {"a": 5, "b": 7}}\n```')
        return LLMResponse(content='I now have the sum.\nFINAL ANSWER: The result is 12.')

    async def stream(self, messages: list[LLMMessage], **kwargs: Any) -> AsyncIterator[str]:
        res = await self.complete(messages, **kwargs)
        yield res.content


async def run_agent_task() -> AgentTaskResult:
    tools = ToolRegistry()  # noqa: F841
    # TODO: Register tool "math.add"
    # TODO: Instantiate ReActAgentLoop with MockLLM and tools
    # TODO: Run task "Calculate 5 + 7" via agent.run_task(...) and return result
    raise NotImplementedError
