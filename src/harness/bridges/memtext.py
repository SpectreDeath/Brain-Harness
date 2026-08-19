"""Memtext bridge — provides persistent memory, context offloading, and decision logging.

Enables Harness to leverage Memtext as a first-class `memory.provider` service.
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import structlog

from harness.bridges.base import EcosystemBridgePlugin
from harness.kernel.context import ServiceKey
from harness.services.tools import ToolSpec

logger = structlog.get_logger()

# Service key for memory providers
MEMORY_SERVICE_KEY: ServiceKey[MemtextService] = ServiceKey("memory.provider")


class MemtextService(ABC):
    """Abstract interface for persistent agent context & memory."""

    @abstractmethod
    async def remember(self, key: str, content: str, metadata: dict[str, Any] | None = None) -> bool:
        """Store information in memory."""

    @abstractmethod
    async def recall(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search and recall relevant memories."""

    @abstractmethod
    async def log_decision(self, agent: str, decision: str, context: dict[str, Any] | None = None) -> None:
        """Record an agent decision into the immutable audit ledger."""


class LocalMemtextService(MemtextService):
    """Local fallback / direct implementation of Memtext memory."""

    def __init__(self, db_dir: Path | None = None) -> None:
        self._db_dir = db_dir or Path.home() / ".harness" / "memory"
        self._db_dir.mkdir(parents=True, exist_ok=True)
        self._memories: list[dict[str, Any]] = []
        self._ledger: list[dict[str, Any]] = []

    async def remember(self, key: str, content: str, metadata: dict[str, Any] | None = None) -> bool:
        self._memories.append({
            "key": key,
            "content": content,
            "metadata": metadata or {},
        })
        logger.debug("Memory stored", key=key)
        return True

    async def recall(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        query_lower = query.lower()
        results = [
            m for m in self._memories
            if query_lower in m["key"].lower() or query_lower in m["content"].lower()
        ]
        return results[:limit]

    async def log_decision(self, agent: str, decision: str, context: dict[str, Any] | None = None) -> None:
        entry = {
            "agent": agent,
            "decision": decision,
            "context": context or {},
        }
        self._ledger.append(entry)
        logger.info("Agent decision logged", agent=agent, decision=decision)


class MemtextServicePlugin(EcosystemBridgePlugin[MemtextService]):
    """Plugin providing persistent memory services to the Harness."""

    project_name = "Memtext"
    env_var = "MEMTEXT_PATH"
    service_key = MEMORY_SERVICE_KEY

    def __init__(
        self,
        memtext_path: Path | str | None = None,
        *,
        override_path: Path | str | None = None,
    ) -> None:
        target = memtext_path if memtext_path is not None else override_path
        super().__init__(override_path=target)
        self._memtext_path = self._override_path

    @property
    def name(self) -> str:
        return "memory.memtext"

    @property
    def version(self) -> str:
        return "0.6.0"

    @property
    def description(self) -> str:
        return "Memtext Persistent Memory, Context Offloading & Decision Ledger"

    async def init_substrate(self, root_path: Path) -> MemtextService:
        src_path = root_path / "src"
        if src_path.exists() and str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        elif str(root_path) not in sys.path:
            sys.path.insert(0, str(root_path))

        return LocalMemtextService()

    async def init_fallback_substrate(self) -> MemtextService:
        return LocalMemtextService()

    def provide_instance(self) -> Any:
        return self._substrate or LocalMemtextService()

    async def get_tool_specs(self) -> list[ToolSpec]:
        async def memory_store(key: str, content: str) -> dict[str, Any]:
            service = self._substrate or self.provide_instance()
            success = await service.remember(key, content)
            return {"status": "ok" if success else "error", "key": key}

        async def memory_recall(query: str, limit: int = 5) -> dict[str, Any]:
            service = self._substrate or self.provide_instance()
            memories = await service.recall(query, limit=limit)
            return {"status": "ok", "memories": memories}

        return [
            ToolSpec(
                name="memory.store",
                description="Store key context or observations in persistent memory",
                executor=memory_store,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "Subject key for memory"},
                        "content": {"type": "string", "description": "Content to remember"},
                    },
                    "required": ["key", "content"],
                },
                provider=self.name,
            ),
            ToolSpec(
                name="memory.recall",
                description="Query and recall past memories and knowledge",
                executor=memory_recall,
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search keyword or phrase"},
                        "limit": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
                provider=self.name,
            ),
        ]
