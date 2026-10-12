"""Session retrieval and query mixin."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from harness.agent.session.models import AgentSession
    from harness.agent.session.store import AgentSessionStore


class SessionQueryMixin:
    """Provides session lookup and root listing operations."""

    store: AgentSessionStore

    async def get_session(self, session_id: str) -> AgentSession | None:
        """Retrieve a session by ID."""
        return await self.store.get(session_id)

    async def list_sessions(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentSession]:
        """List persisted sessions."""
        return await self.store.list(status=status, limit=limit, offset=offset)

    async def list_root_sessions(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentSession]:
        """List root-level sessions (excluding child sub-agent executions)."""
        all_sessions = await self.store.list(status=status, limit=1000)
        root_sessions = [s for s in all_sessions if s.parent_session_id is None]
        return root_sessions[offset : offset + limit]
