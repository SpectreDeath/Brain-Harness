"""Authoritative Agent Session Management and Persistent Trajectory Store package (decomposed).

Exposes typed domain models, storage backends, tree exporters, session scopes,
lifecycle manager, and IoC plugin. Preserves 100% backward compatibility for all
module-level imports from `harness.agent.session`.
"""

from __future__ import annotations

# Re-exported base agent primitives for backward compatibility
from harness.agent.base import (
    AgentStep,
    AgentTaskResult,
    AgentTrajectory,
)

# 1. Models & Tree Structures
from harness.agent.session.models import (
    AgentSession,
    SessionTreeNode,
    SessionTreeSnapshot,
)

# 2. Storage Adapters
from harness.agent.session.store import (
    AgentSessionStore,
    InMemoryAgentSessionStore,
    StorageBackedSessionStore,
)

# 3. Exporter & Transcript Engine
from harness.agent.session.exporter import SessionTreeExporter

# 4. Async Execution Scope
from harness.agent.session.scope import AgentSessionScope

# 5. Lifecycle Manager & ServiceKey
from harness.agent.session.manager import (
    AGENT_SESSION_MANAGER_KEY,
    AgentSessionManager,
)

# 6. IoC Plugin
from harness.agent.session.plugin import AgentSessionPlugin

__all__ = [
    # Base Re-exports
    "AgentStep",
    "AgentTaskResult",
    "AgentTrajectory",
    # Models
    "AgentSession",
    "SessionTreeNode",
    "SessionTreeSnapshot",
    # Store
    "AgentSessionStore",
    "InMemoryAgentSessionStore",
    "StorageBackedSessionStore",
    # Exporter
    "SessionTreeExporter",
    # Scope
    "AgentSessionScope",
    # Manager
    "AGENT_SESSION_MANAGER_KEY",
    "AgentSessionManager",
    # Plugin
    "AgentSessionPlugin",
]
