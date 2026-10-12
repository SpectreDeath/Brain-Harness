"""Authoritative AgentSessionManager subpackage (decomposed)."""

from __future__ import annotations

from harness.agent.session.manager.creation import SessionCreationMixin
from harness.agent.session.manager.export import SessionExportMixin
from harness.agent.session.manager.hierarchy import SessionHierarchyMixin
from harness.agent.session.manager.lifecycle import SessionLifecycleMixin
from harness.agent.session.manager.protocols import AGENT_SESSION_MANAGER_KEY
from harness.agent.session.manager.query import SessionQueryMixin
from harness.agent.session.manager.resolvers import resolve_session_manager
from harness.agent.session.manager.service import AgentSessionManager

__all__ = [
    "AGENT_SESSION_MANAGER_KEY",
    "AgentSessionManager",
    "SessionCreationMixin",
    "SessionExportMixin",
    "SessionHierarchyMixin",
    "SessionLifecycleMixin",
    "SessionQueryMixin",
    "resolve_session_manager",
]
