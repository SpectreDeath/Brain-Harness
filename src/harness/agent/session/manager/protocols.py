"""ServiceKey definition for AgentSessionManager."""

from __future__ import annotations

from typing import TYPE_CHECKING

from harness.kernel.context import ServiceKey

if TYPE_CHECKING:
    from harness.agent.session.manager.service import AgentSessionManager

AGENT_SESSION_MANAGER_KEY: ServiceKey[AgentSessionManager] = ServiceKey("agent.session_manager")
