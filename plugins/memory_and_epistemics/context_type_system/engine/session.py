"""Session management and state persistence for isolated ContextStore instances."""

from __future__ import annotations

import time
from typing import Any, Dict, List

from .store import ContextStore


class ContextSessionManager:
    """Manages independent ContextStore sessions by session_id with snapshot persistence."""

    def __init__(self) -> None:
        self._sessions: Dict[str, ContextStore] = {}

    def get_session(self, session_id: str) -> ContextStore:
        if session_id not in self._sessions:
            self._sessions[session_id] = ContextStore()
        return self._sessions[session_id]

    def reset_session(self, session_id: str) -> None:
        if session_id in self._sessions:
            del self._sessions[session_id]

    def list_sessions(self) -> List[str]:
        return list(self._sessions.keys())

    def export_session(self, session_id: str) -> dict[str, Any]:
        """Export session state as a portable snapshot."""
        store = self.get_session(session_id)
        return {
            "session_id": session_id,
            "exported_at": time.time(),
            "state": store.export_state(),
        }

    def import_session(self, session_id: str, data: dict[str, Any]) -> None:
        """Restore a session from a snapshot dictionary."""
        state = data.get("state", data)
        self._sessions[session_id] = ContextStore.from_dict(state)
