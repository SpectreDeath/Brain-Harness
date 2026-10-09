"""Contract verification tests for ReAct agent loop modular decomposition (Cycle 23)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import typing

import pytest

from harness.agent.base import AGENT_LOOP_KEY, AgentTrajectory
from harness.kernel.context import ServiceContext
from harness.services.llm import LLMMessage, LLMResponse, LLMService, LLM_SERVICE_KEY
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry


@pytest.mark.unit
def test_submodule_line_counts():
    """Verify all decomposed submodules in react/ obey the < 200 line budget (Rule 11)."""
    react_dir = Path("src/harness/agent/react")
    assert react_dir.is_dir()
    py_files = list(react_dir.glob("*.py"))
    assert len(py_files) >= 8

    for py_file in py_files:
        lines = py_file.read_text(encoding="utf-8").splitlines()
        assert len(lines) < 200, f"{py_file.name} has {len(lines)} lines (budget is < 200)"


@pytest.mark.unit
def test_direct_submodule_imports():
    """Verify all decomposed submodules can be imported independently without circular dependencies."""
    from harness.agent.react.dispatch import (
        dispatch_native_tool_calls,
        dispatch_text_fallback_action,
    )
    from harness.agent.react.engine import StepExecutionEngine
    from harness.agent.react.loop import ReActAgentLoop
    from harness.agent.react.plugin import ReActAgentPlugin, plugin
    from harness.agent.react.prompting import (
        build_react_initial_messages,
        extract_action_from_thought,
    )
    from harness.agent.react.resolvers import resolve_react_agent_loop
    from harness.agent.react.transactions import invoke_tool_transactional

    assert dispatch_native_tool_calls is not None
    assert dispatch_text_fallback_action is not None
    assert StepExecutionEngine is not None
    assert ReActAgentLoop is not None
    assert ReActAgentPlugin is not None
    assert plugin is not None
    assert build_react_initial_messages is not None
    assert extract_action_from_thought is not None
    assert resolve_react_agent_loop is not None
    assert invoke_tool_transactional is not None


@pytest.mark.unit
def test_facade_re_exports_and_backward_compatibility():
    """Verify package __init__.py re-exports all legacy and new domain symbols."""
    from harness.agent.react import (
        ReActAgentLoop,
        ReActAgentPlugin,
        StepExecutionEngine,
        build_react_initial_messages,
        dispatch_native_tool_calls,
        dispatch_text_fallback_action,
        extract_action_from_thought,
        invoke_tool_transactional,
        plugin,
        resolve_react_agent_loop,
    )

    assert ReActAgentLoop is not None
    assert ReActAgentPlugin is not None
    assert StepExecutionEngine is not None
    assert build_react_initial_messages is not None
    assert dispatch_native_tool_calls is not None
    assert dispatch_text_fallback_action is not None
    assert extract_action_from_thought is not None
    assert invoke_tool_transactional is not None
    assert plugin is not None
    assert resolve_react_agent_loop is not None


@pytest.mark.unit
def test_agent_package_facade_compatibility():
    """Verify top-level harness.agent re-exports continue working seamlessly."""
    from harness.agent import (
        ReActAgentLoop,
        ReActAgentPlugin,
        StepExecutionEngine,
    )

    assert ReActAgentLoop is not None
    assert ReActAgentPlugin is not None
    assert StepExecutionEngine is not None


@pytest.mark.unit
def test_plugin_singleton_export():
    """Verify module-level plugin singleton exists and declares proper metadata (Rule 45)."""
    from harness.agent.react import plugin, ReActAgentPlugin

    assert isinstance(plugin, ReActAgentPlugin)
    assert plugin.name == "agent.react"
    assert AGENT_LOOP_KEY in plugin.provides
    assert LLM_SERVICE_KEY in plugin.requires
    assert TOOL_REGISTRY_KEY in plugin.requires


@pytest.mark.unit
def test_step_engine_type_hints():
    """Verify StepExecutionEngine._invoke_tool_safely type hints evaluation."""
    from harness.agent.react import StepExecutionEngine

    hints = typing.get_type_hints(StepExecutionEngine._invoke_tool_safely)
    assert hints.get("action_name") is str
    assert "action_input" in hints


@pytest.mark.unit
def test_four_pass_action_extraction():
    """Verify extract_action_from_thought handles all 4 formats with in-flight repair (Rule 21)."""
    from harness.agent.react import extract_action_from_thought

    # 1. JSON fence
    fence = 'Thinking...\n```json\n{"action": "fs.read", "input": {"path": "a.txt"}}\n```'
    act, inp = extract_action_from_thought(fence)
    assert act == "fs.read"
    assert inp == {"path": "a.txt"}

    # 2. XML <tool_call> tag
    xml = '<tool_call>{"action": "grep", "input": {"query": "test"}}</tool_call>'
    act, inp = extract_action_from_thought(xml)
    assert act == "grep"
    assert inp == {"query": "test"}

    # 3. Raw JSON object with auto-repair (trailing comma + unclosed brace)
    malformed = '{"action": "calc", "input": {"val": 42,}'
    act, inp = extract_action_from_thought(malformed)
    assert act == "calc"
    assert inp == {"val": 42}

    # 4. Outermost brace scan
    nested = 'Prefix reasoning: {"action": "echo", "input": {"msg": "hi"}} Suffix notes'
    act, inp = extract_action_from_thought(nested)
    assert act == "echo"
    assert inp == {"msg": "hi"}

    # 5. No action found
    act, inp = extract_action_from_thought("Just general thoughts with no json")
    assert act is None
    assert inp == {}


@pytest.mark.unit
def test_single_seam_resolver():
    """Verify resolve_react_agent_loop single-seam resolver factory (Rule 58)."""
    from harness.agent.react import resolve_react_agent_loop, ReActAgentLoop

    class DummyLLM(LLMService):
        async def complete(self, messages: list[LLMMessage], **kwargs: Any) -> LLMResponse:
            return LLMResponse(content="FINAL ANSWER: Done")

        async def stream(self, messages: list[LLMMessage], **kwargs: Any) -> Any:
            yield ""

    ctx = ServiceContext()
    ctx.provide(LLM_SERVICE_KEY, DummyLLM())
    ctx.provide(TOOL_REGISTRY_KEY, ToolRegistry())

    loop = resolve_react_agent_loop(ctx)
    assert isinstance(loop, ReActAgentLoop)

    # Calling resolve again returns the existing provided service if registered
    ctx.provide(AGENT_LOOP_KEY, loop)
    resolved_again = resolve_react_agent_loop(ctx)
    assert resolved_again is loop


@pytest.mark.asyncio
@pytest.mark.unit
async def test_transactional_tool_execution():
    """Verify StepExecutionEngine executes tools within context transactions."""
    from harness.agent.react import StepExecutionEngine

    ctx = ServiceContext()
    tools = ToolRegistry()

    def greet(name: str) -> dict[str, str]:
        return {"greeting": f"Hello, {name}!"}

    tools.register(name="greet", description="greet user", executor=greet)
    engine = StepExecutionEngine(tools=tools, context=ctx)

    obs = await engine._invoke_tool_safely("greet", {"name": "Alice"})
    assert obs == {"status": "ok", "result": {"greeting": "Hello, Alice!"}}


@pytest.mark.unit
def test_initial_messages_construction():
    """Verify build_initial_messages builds prompt schemas and task payload."""
    from harness.agent.react import StepExecutionEngine

    tools = ToolRegistry()
    tools.register(name="test_tool", description="A test tool", executor=lambda: None)
    engine = StepExecutionEngine(tools=tools)

    msgs = engine.build_initial_messages("Solve the puzzle")
    assert len(msgs) == 2
    assert msgs[0].role == "system"
    assert "test_tool" in msgs[0].content
    assert msgs[1].role == "user"
    assert "Solve the puzzle" in msgs[1].content
