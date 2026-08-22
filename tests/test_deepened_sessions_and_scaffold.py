"""Tests for deepened Agent Session State Machine and Plugin Scaffold Engine seams."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from harness.agent.base import (
    AgentStep,
)
from harness.agent.react import ReActAgentLoop
from harness.agent.session import (
    AgentSession,
    AgentSessionManager,
    InMemoryAgentSessionStore,
    StorageBackedSessionStore,
)
from harness.creator.dynamic import DynamicPluginBuilder
from harness.creator.scaffold import PluginScaffoldEngine, ScaffoldOptions
from harness.events.bus import EventBus
from harness.events.types import EventType
from harness.services.llm import LLMMessage, LLMResponse, LLMService
from harness.services.storage import SQLiteStorageService
from harness.services.tools import ToolRegistry, ToolSpec


class MockLLM(LLMService):
    def __init__(self, responses: list[LLMResponse] | None = None) -> None:
        self.responses = list(responses or [])
        self.call_count = 0
        self.recorded_messages: list[list[LLMMessage]] = []

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        self.call_count += 1
        self.recorded_messages.append(messages)
        if self.responses:
            return self.responses.pop(0)
        return LLMResponse(content="FINAL ANSWER: Done successfully")

    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> Any:
        yield "Mock stream chunk"


@pytest.mark.unit
def test_agent_session_lifecycle_and_serialization() -> None:
    session = AgentSession(
        session_id="sess_123",
        task="Calculate Fibonacci numbers",
        metadata={"user_id": "u42"},
    )
    assert session.status == "running"
    assert session.session_id == "sess_123"

    step = AgentStep(
        step_number=1,
        thought="Calculating step 1",
        action="calc",
        action_input={"n": 5},
        observation={"fib": 5},
    )
    session.add_step(step)
    assert len(session.steps) == 1

    session.mark_completed("Fibonacci 5 is 5", total_tokens=150)
    assert session.status == "completed"
    assert session.final_answer == "Fibonacci 5 is 5"
    assert session.completed_at is not None

    # Serialization roundtrip
    data = session.to_dict()
    assert data["session_id"] == "sess_123"
    assert data["status"] == "completed"
    assert len(data["steps"]) == 1

    reconstituted = AgentSession.from_dict(data)
    assert reconstituted.session_id == "sess_123"
    assert reconstituted.status == "completed"
    assert len(reconstituted.steps) == 1
    assert reconstituted.steps[0].action == "calc"

    # Conversion to trajectory and result
    traj = session.to_trajectory()
    assert traj.session_id == "sess_123"
    assert traj.status == "completed"

    res = session.to_result()
    assert res.session_id == "sess_123"
    assert res.status == "completed"

    # Markdown export
    md = session.to_markdown()
    assert "# Agent Execution Session: `sess_123`" in md
    assert "Calculate Fibonacci numbers" in md
    assert "### Step 1" in md
    assert "Fibonacci 5 is 5" in md


@pytest.mark.asyncio
async def test_in_memory_session_store() -> None:
    store = InMemoryAgentSessionStore()
    sess1 = AgentSession(session_id="s1", task="Task 1")
    sess2 = AgentSession(session_id="s2", task="Task 2", status="completed")

    await store.save(sess1)
    await store.save(sess2)

    retrieved = await store.get("s1")
    assert retrieved is not None
    assert retrieved.task == "Task 1"

    all_sessions = await store.list()
    assert len(all_sessions) == 2

    completed = await store.list(status="completed")
    assert len(completed) == 1
    assert completed[0].session_id == "s2"

    deleted = await store.delete("s1")
    assert deleted is True
    assert await store.get("s1") is None


@pytest.mark.asyncio
async def test_storage_backed_session_store(tmp_path: Path) -> None:
    db_path = tmp_path / "sessions.db"
    storage = SQLiteStorageService(db_path=db_path)
    store = StorageBackedSessionStore(storage=storage)

    sess = AgentSession(
        session_id="persisted_1",
        task="Database backup",
        metadata={"priority": "high"},
    )
    sess.add_step(AgentStep(step_number=1, thought="Backing up tables"))
    sess.mark_completed("Backup finished")

    await store.save(sess)

    fetched = await store.get("persisted_1")
    assert fetched is not None
    assert fetched.session_id == "persisted_1"
    assert fetched.task == "Database backup"
    assert fetched.status == "completed"
    assert len(fetched.steps) == 1

    listed = await store.list(status="completed")
    assert len(listed) >= 1
    assert any(s.session_id == "persisted_1" for s in listed)

    del_res = await store.delete("persisted_1")
    assert del_res is True
    assert await store.get("persisted_1") is None


@pytest.mark.asyncio
async def test_agent_session_manager_orchestration() -> None:
    event_bus = EventBus()
    events_received: list[Any] = []

    async def on_event(evt: Any) -> None:
        events_received.append(evt)

    event_bus.on(EventType.AGENT_TASK_STARTED, on_event)
    event_bus.on(EventType.AGENT_STEP_COMPLETED, on_event)
    event_bus.on(EventType.AGENT_TASK_COMPLETED, on_event)

    mgr = AgentSessionManager(event_bus=event_bus)
    sess = await mgr.create_session("Automated report generation", session_id="report_001")
    assert sess.session_id == "report_001"
    assert sess.status == "running"

    step = AgentStep(step_number=1, thought="Querying database", action="query_db")
    sess = await mgr.record_step("report_001", step)
    assert len(sess.steps) == 1

    sess = await mgr.complete_session("report_001", "Report compiled successfully", total_tokens=300)
    assert sess.status == "completed"

    # Export formats
    json_export = await mgr.export_session("report_001", format="json")
    parsed = json.loads(json_export)
    assert parsed["session_id"] == "report_001"
    assert parsed["status"] == "completed"

    md_export = await mgr.export_session("report_001", format="markdown")
    assert "Automated report generation" in md_export
    assert "Querying database" in md_export

    # Verify telemetry events fired
    assert len(events_received) >= 3


@pytest.mark.asyncio
async def test_react_agent_loop_with_session_manager() -> None:
    tools = ToolRegistry()

    def multiply(a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b

    tools.register(ToolSpec.from_callable(multiply, name="multiply", provider="math"))

    llm = MockLLM(
        responses=[
            LLMResponse(
                content="I need to multiply 6 by 7",
                tool_calls=[
                    {
                        "id": "tc1",
                        "name": "multiply",
                        "arguments": {"a": 6, "b": 7},
                    }
                ],
            ),
            LLMResponse(content="FINAL ANSWER: The answer is 42"),
        ]
    )

    mgr = AgentSessionManager()
    loop = ReActAgentLoop(
        llm=llm,
        tool_registry=tools,
        session_manager=mgr,
    )

    result = await loop.run_task(
        "Calculate 6 * 7",
        context={"session_id": "math_sess_42"},
    )

    assert result.status == "completed"
    assert "42" in result.final_answer
    assert result.session_id == "math_sess_42"

    persisted = await mgr.get_session("math_sess_42")
    assert persisted is not None
    assert persisted.status == "completed"
    assert len(persisted.steps) == 2
    assert persisted.steps[0].action == "multiply"
    assert persisted.steps[0].observation == {"status": "ok", "result": 42}
    assert "FINAL ANSWER:" in persisted.steps[1].thought


@pytest.mark.unit
def test_plugin_scaffold_engine_python(tmp_path: Path) -> None:
    engine = PluginScaffoldEngine()
    opts = ScaffoldOptions(
        name="weather-fetcher",
        description="Fetches current weather telemetry",
        language="python",
        tools=["get_forecast", "get_alerts"],
        dependencies=["httpx>=0.27.0"],
    )

    target = tmp_path / "weather_plugin"
    engine.scaffold(target, options=opts)

    assert (target / "plugin.json").exists()
    assert (target / "main.py").exists()
    assert (target / "QUICKSTART.md").exists()
    assert (target / "requirements.txt").exists()
    assert (target / "tests" / "test_plugin.py").exists()

    manifest_data = json.loads((target / "plugin.json").read_text(encoding="utf-8"))
    assert manifest_data["name"] == "weather-fetcher"
    assert manifest_data["entrypoint"] == "main.py"
    assert "httpx>=0.27.0" in manifest_data["dependencies"]

    main_py = (target / "main.py").read_text(encoding="utf-8")
    assert "def get_forecast" in main_py
    assert "def get_alerts" in main_py

    reqs = (target / "requirements.txt").read_text(encoding="utf-8")
    assert "httpx>=0.27.0" in reqs


@pytest.mark.unit
def test_plugin_scaffold_engine_javascript(tmp_path: Path) -> None:
    engine = PluginScaffoldEngine()
    opts = ScaffoldOptions(
        name="crypto-signer",
        description="Signs payloads using ECDSA",
        language="javascript",
        tools=["sign_payload", "verify_signature"],
        dependencies=["ethers"],
    )

    target = tmp_path / "crypto_plugin"
    engine.scaffold(target, options=opts)

    assert (target / "plugin.json").exists()
    assert (target / "index.js").exists()
    assert (target / "package.json").exists()
    assert (target / "tests" / "plugin.test.js").exists()

    js_code = (target / "index.js").read_text(encoding="utf-8")
    assert "export async function sign_payload" in js_code
    assert "export async function verify_signature" in js_code

    pkg_json = json.loads((target / "package.json").read_text(encoding="utf-8"))
    assert pkg_json["name"] == "crypto-signer"
    assert "ethers" in pkg_json["dependencies"]


@pytest.mark.unit
def test_dynamic_plugin_builder_scaffold_delegation(tmp_path: Path) -> None:
    target = tmp_path / "builder_scaffolded"
    DynamicPluginBuilder.scaffold_project(
        target,
        name="quick-service",
        description="Quick service plugin",
        language="python",
        tools=["process"],
    )

    assert (target / "plugin.json").exists()
    assert (target / "main.py").exists()
    assert (target / "QUICKSTART.md").exists()
    assert (target / "requirements.txt").exists()

    manifest_data = json.loads((target / "plugin.json").read_text(encoding="utf-8"))
    assert len(manifest_data["entrypoints"]) == 1
    assert manifest_data["entrypoints"][0]["name"] == "process"


@pytest.mark.asyncio
async def test_scaffolded_plugin_sandboxed_tool_mount(tmp_path: Path) -> None:
    from harness.kernel.context import ServiceContext
    from harness.plugins.loader import PluginLoader
    from harness.plugins.sandboxed import SandboxedPlugin
    from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistryPlugin

    target = tmp_path / "calc_scaffolded"
    engine = PluginScaffoldEngine()
    engine.scaffold(
        target,
        name="calc-plugin",
        language="python",
        tools=["calculate"],
    )

    loader = PluginLoader(plugin_dirs=[tmp_path])
    manifest = loader.get_manifest("calc-plugin")
    assert manifest is not None
    assert len(manifest.entrypoints) == 1
    assert manifest.entrypoints[0].name == "calculate"

    # Load into context
    ctx = ServiceContext()
    tools_plugin = ToolRegistryPlugin()
    await tools_plugin.on_load(ctx)

    plugin = SandboxedPlugin(manifest, target)
    await plugin.on_load(ctx)
    await plugin.on_enable()

    tool_reg = ctx.require(TOOL_REGISTRY_KEY)
    assert "calc-plugin.calculate" in tool_reg

    res = await tool_reg.invoke("calc-plugin.calculate", {"task": "2+2"})
    assert res["status"] == "ok"
    assert res["result"]["action"] == "calculate"
    assert "Executed calculate with 2+2" in res["result"]["result"]

    await plugin.on_disable()
    assert "calc-plugin.calculate" not in tool_reg
