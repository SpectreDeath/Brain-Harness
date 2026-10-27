"""Session export mixin for JSON and Markdown serialization.

Architectural Layering:
- This mixin (`SessionExportMixin`) binds `export_session` to `AgentSessionManager`.
- It fetches the session from `self.store` and delegates formatting to the pure
  stateless serializer `SessionTreeExporter` in `harness.agent.session.exporter`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from harness.agent.session.exporter import SessionTreeExporter

if TYPE_CHECKING:
    from harness.agent.session.store import AgentSessionStore


class SessionExportMixin:
    """Provides JSON and Markdown export serialization."""

    store: AgentSessionStore

    async def export_session(self, session_id: str, format: str = "json") -> str:
        """Export an agent execution session to JSON or Markdown."""
        session = await self.store.get(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found")

        if format.lower() in ("markdown", "md"):
            return SessionTreeExporter.to_markdown(session)
        return SessionTreeExporter.to_json(session)
