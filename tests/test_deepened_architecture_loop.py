"""Tests for deepened architecture loop — AgentSessionScope and EcosystemBridgeCatalog."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from harness.agent.base import AgentStep
from harness.agent.session import (
    AGENT_SESSION_MANAGER_KEY,
    AgentSession,
    AgentSessionManager,
    AgentSessionPlugin,
    AgentSessionScope,
    InMemoryAgentSessionStore,
)
from harness.bridges.base import EcosystemBridgeCatalog, EcosystemBridgePlugin
from harness.events.bus import EventBus
from harness.events.types import EventType, HarnessEvent
from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.runtime import HarnessRuntime
from harness.services.llm import LiteLLMService, LLMResponse


class DummyLLM(LiteLLMService):
    """Stub LLM for testing agent loop execution."""

    def __init__(self, responses: list[str] | None = None) -> None:
        self.responses = list(responses or ["FINAL ANSWER: Done successfully!"])
        self.idx = 0

    async def complete(self, messages: Any, **kwargs: Any) -> LLMResponse:
        content = self.responses[min(self.idx, len(self.responses) - 1)]
        self.idx += 1
        return LLMResponse(content=content)


@pytest.mark.asyncio
async def test_agent_session_scope_lifecycle() -> None:
    """Test standard execution lifecycle via AgentSessionScope."""
    bus = EventBus()
    store = InMemoryAgentSessionStore()
    mgr = AgentSessionManager(store=store, event_bus=bus)

    emitted_events: list[HarnessEvent] = []

    def _on_event(evt: HarnessEvent) -> None:
        emitted_events.append(evt)

    bus.on(EventType.AGENT_TASK_STARTED, _on_event)
    bus.on(EventType.AGENT_STEP_COMPLETED, _on_event)
    bus.on(EventType.AGENT_TASK_COMPLETED, _on_event)

    async with mgr.session_scope("Analyze dataset", agent_name="agent.test") as scope:
        assert isinstance(scope, AgentSessionScope)
        assert scope.task == "Analyze dataset"
        assert scope.status == "running"

        step = AgentStep(
            step_number=1,
            thought="Step 1 thought",
            action="dataset.load",
            action_input={"file": "data.csv"},
            observation={"rows": 100},
        )
        await scope.record_step(step)
        assert len(scope.steps) == 1

        scope.mark_completed("Data analyzed completely.", total_tokens=150)

    # Verify session persisted in store
    saved = await store.get(scope.session_id)
    assert saved is not None
    assert saved.status == "completed"
    assert saved.final_answer == "Data analyzed completely."
    assert saved.total_tokens == 150
    assert len(saved.steps) == 1

    # Verify events
    event_types = [e.event_type for e in emitted_events]
    assert EventType.AGENT_TASK_STARTED in event_types
    assert EventType.AGENT_STEP_COMPLETED in event_types
    assert EventType.AGENT_TASK_COMPLETED in event_types


@pytest.mark.asyncio
async def test_agent_session_scope_error_handling() -> None:
    """Test error handling in AgentSessionScope."""
    bus = EventBus()
    store = InMemoryAgentSessionStore()
    mgr = AgentSessionManager(store=store, event_bus=bus)

    failed_events: list[HarnessEvent] = []
    bus.on(EventType.AGENT_TASK_FAILED, lambda e: failed_events.append(e))

    session_id_recorded = None
    with pytest.raises(ValueError, match="Simulated execution crash"):
        async with mgr.session_scope("Failing task", agent_name="agent.test") as scope:
            session_id_recorded = scope.session_id
            raise ValueError("Simulated execution crash")

    saved = await store.get(session_id_recorded)
    assert saved is not None
    assert saved.status == "error"
    assert "Simulated execution crash" in saved.final_answer
    assert len(failed_events) == 1


@pytest.mark.asyncio
async def test_agent_session_scope_max_steps() -> None:
    """Test max steps status transition in AgentSessionScope."""
    mgr = AgentSessionManager()
    async with mgr.session_scope("Long task") as scope:
        scope.mark_max_steps("Hit step limit fallback")

    saved = await mgr.get_session(scope.session_id)
    assert saved is not None
    assert saved.status == "max_steps_reached"
    assert saved.final_answer == "Hit step limit fallback"


def test_ecosystem_bridge_catalog_registration() -> None:
    """Test that ecosystem bridges self-register into EcosystemBridgeCatalog."""
    bridges = EcosystemBridgeCatalog.list_bridges()
    bridge_names = [getattr(b, "project_name", "") for b in bridges]

    assert "em-cubed" in bridge_names
    assert "Memtext" in bridge_names
    assert "Skill Flywheel" in bridge_names

    em_cls = EcosystemBridgeCatalog.get_bridge("em-cubed")
    assert em_cls is not None
    assert em_cls.project_name == "em-cubed"

    status = EcosystemBridgeCatalog.status()
    assert "em-cubed" in status
    assert "Memtext" in status
    assert "Skill Flywheel" in status
    assert "available" in status["em-cubed"]
    assert "env_var" in status["em-cubed"]


def test_ecosystem_bridge_catalog_discover_plugins() -> None:
    """Test discovery and instantiation of bridge plugins."""
    plugins = EcosystemBridgeCatalog.discover_available_plugins(include_unresolved=True)
    plugin_names = [p.name for p in plugins]

    assert "bridge.em_cubed" in plugin_names
    assert "memory.memtext" in plugin_names
    assert "bridge.flywheel" in plugin_names


@pytest.mark.asyncio
async def test_runtime_integration_with_deepened_seams() -> None:
    """Integration test checking runtime auto-discovery, agent session scope, and export."""
    custom_llm = DummyLLM(responses=["FINAL ANSWER: Integration task solved."])

    async with HarnessRuntime.create(db_path=":memory:", fallback_llm=custom_llm) as runtime:
        # Check that bridges were auto-mounted from catalog
        assert runtime.context.has(ServiceKey("bridge.em_cubed"))
        assert runtime.context.has(ServiceKey("memory.provider"))
        assert runtime.context.has(ServiceKey("bridge.flywheel"))

        # Check agent execution creates session and records trajectory
        result = await runtime.run_task("Deepened architecture test task")
        assert result.status == "completed"
        assert "Integration task solved" in result.final_answer

        session_id = result.session_id
        assert session_id is not None

        # Verify session can be retrieved and exported from session manager
        session = await runtime.sessions.get_session(session_id)
        assert session is not None
        assert session.status == "completed"

        md_export = await runtime.export_session(session_id, format="markdown")
        assert f"Agent Execution Session: `{session_id}`" in md_export
        assert "Deepened architecture test task" in md_export

        json_export = await runtime.export_session(session_id, format="json")
        assert session_id in json_export
