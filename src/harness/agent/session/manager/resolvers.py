"""Single-seam service resolver for AgentSessionManager per Rule 58."""

from __future__ import annotations

from harness.agent.session.manager.protocols import AGENT_SESSION_MANAGER_KEY
from harness.agent.session.manager.service import AgentSessionManager
from harness.kernel.context import ServiceContext


def resolve_session_manager(
    context: ServiceContext | None = None,
) -> AgentSessionManager:
    """Resolve AgentSessionManager from IoC container if available, else instantiate default."""
    if context and context.has(AGENT_SESSION_MANAGER_KEY):
        return context.require(AGENT_SESSION_MANAGER_KEY)
    return AgentSessionManager(context=context)
