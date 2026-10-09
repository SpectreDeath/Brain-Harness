"""Single-seam resolver for ReAct agent loop services (Rule 58)."""

from __future__ import annotations

from harness.agent.base import AGENT_LOOP_KEY
from harness.kernel.context import ServiceContext
from harness.services.llm import LLM_SERVICE_KEY, LLMService
from harness.services.tools import TOOL_REGISTRY_KEY, ToolRegistry

from .loop import ReActAgentLoop


def resolve_react_agent_loop(context: ServiceContext) -> ReActAgentLoop:
    """Resolve or instantiate the ReActAgentLoop service from the container."""
    existing = context.optional(AGENT_LOOP_KEY)
    if existing is not None and isinstance(existing, ReActAgentLoop):
        return existing

    llm: LLMService = context.require(LLM_SERVICE_KEY)
    tools: ToolRegistry = context.require(TOOL_REGISTRY_KEY)

    from harness.agent.context_optimizer import (
        AGENT_CONTEXT_OPTIMIZER_KEY,
        AgentContextOptimizer,
    )
    from harness.agent.session import (
        AGENT_SESSION_MANAGER_KEY,
        AgentSessionManager,
    )
    from harness.events.bus import EVENT_BUS_KEY, EventBus

    event_bus: EventBus | None = context.optional(EVENT_BUS_KEY)
    session_manager: AgentSessionManager | None = context.optional(
        AGENT_SESSION_MANAGER_KEY
    )
    optimizer: AgentContextOptimizer | None = context.optional(
        AGENT_CONTEXT_OPTIMIZER_KEY
    )

    return ReActAgentLoop(
        llm=llm,
        tool_registry=tools,
        event_bus=event_bus,
        session_manager=session_manager,
        context=context,
        optimizer=optimizer,
    )
