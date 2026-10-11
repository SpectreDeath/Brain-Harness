"""Runtime service resolution and IoC accessors mixin."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, TypeVar

from harness.kernel.context import ServiceContext, ServiceKey
from harness.kernel.runtime.tools import export_runtime_session

if TYPE_CHECKING:
    from harness.agent.session import AgentSessionManagerService

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

T = TypeVar("T")


class RuntimeServicesMixin:
    """Service resolution and accessor properties for HarnessRuntime."""

    _context: ServiceContext

    @property
    def tools(self) -> Any | None:
        """Tool registry service if available."""
        from harness.services.tools import TOOL_REGISTRY_KEY

        return self._context.optional(TOOL_REGISTRY_KEY)

    @property
    def storage(self) -> Any | None:
        """Storage service if available."""
        from harness.services.storage import STORAGE_SERVICE_KEY

        return self._context.optional(STORAGE_SERVICE_KEY)

    @property
    def llm(self) -> Any | None:
        """LLM service if available."""
        from harness.services.llm import LLM_SERVICE_KEY

        return self._context.optional(LLM_SERVICE_KEY)

    @property
    def agent(self) -> Any | None:
        """Agent loop service if available."""
        from harness.agent.base import AGENT_LOOP_KEY

        return self._context.optional(AGENT_LOOP_KEY)

    @property
    def sessions(self) -> AgentSessionManagerService | None:
        """Agent session manager service if available."""
        from harness.agent.session import AGENT_SESSION_MANAGER_KEY

        return self._context.optional(AGENT_SESSION_MANAGER_KEY)

    async def export_session(self, session_id: str, format: str = "json") -> str:
        """Export an agent execution session to JSON or Markdown."""
        return await export_runtime_session(self, session_id, format=format)  # type: ignore[arg-type]

    def require(self, key: ServiceKey[T]) -> T:
        """Resolve a required service from the context."""
        return self._context.require(key)

    def optional(self, key: ServiceKey[T]) -> T | None:
        """Resolve an optional service from the context."""
        return self._context.optional(key)

    def provide(
        self,
        key: ServiceKey[T],
        instance: T,
        *,
        provider: str | None = None,
        allow_override: bool = False,
    ) -> None:
        """Register a service into the context."""
        self._context.provide(key, instance, provider=provider, allow_override=allow_override)


__all__ = ["RuntimeServicesMixin"]
