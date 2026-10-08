"""Session persistence store abstractions and backend implementations.

Provides in-memory volatile and storage-backed durable session adapters.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from harness.agent.session.models import AgentSession


class AgentSessionStore(ABC):
    """Abstract interface for agent session storage backends."""

    @abstractmethod
    async def save(self, session: AgentSession) -> None:
        """Save or update an agent session."""

    @abstractmethod
    async def get(self, session_id: str) -> AgentSession | None:
        """Retrieve a session by its unique ID."""

    @abstractmethod
    async def list(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentSession]:
        """List sessions optionally filtered by status."""

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Delete a session by ID."""


class InMemoryAgentSessionStore(AgentSessionStore):
    """Volatile in-memory implementation of AgentSessionStore."""

    def __init__(self) -> None:
        self._sessions: dict[str, AgentSession] = {}

    async def save(self, session: AgentSession) -> None:
        self._sessions[session.session_id] = session

    async def get(self, session_id: str) -> AgentSession | None:
        return self._sessions.get(session_id)

    async def list(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentSession]:
        items = list(self._sessions.values())
        if status:
            items = [s for s in items if s.status == status]
        # Sort descending by created_at
        items.sort(key=lambda s: s.created_at, reverse=True)
        return items[offset : offset + limit]

    async def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None


class StorageBackedSessionStore(AgentSessionStore):
    """Persistent session store backed by the StorageService."""

    def __init__(self, storage: Any, prefix: str = "agent:session:") -> None:
        self.storage = storage
        self.prefix = prefix

    def _key(self, session_id: str) -> str:
        return f"{self.prefix}{session_id}"

    async def save(self, session: AgentSession) -> None:
        data = session.to_dict()
        await self.storage.set(self._key(session.session_id), data)

    async def get(self, session_id: str) -> AgentSession | None:
        data = await self.storage.get(self._key(session_id))
        if data is None:
            return None
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                return None
        return AgentSession.from_dict(data)

    async def list(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AgentSession]:
        keys = await self.storage.list_keys(prefix=self.prefix)
        sessions: list[AgentSession] = []
        for key in keys:
            data = await self.storage.get(key)
            if data is not None:
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except Exception:
                        continue
                sess = AgentSession.from_dict(data)
                if status is None or sess.status == status:
                    sessions.append(sess)

        sessions.sort(key=lambda s: s.created_at, reverse=True)
        return sessions[offset : offset + limit]

    async def delete(self, session_id: str) -> bool:
        return bool(await self.storage.delete(self._key(session_id)))
