"""Micro-kernel plugin provider registering Skill Registry and Knowledge Graph services."""

from __future__ import annotations

from typing import Any

import structlog

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.skill_clustering import SKILL_CLUSTERING_KEY
from harness.services.skill_graph.protocols import (
    SKILL_GRAPH_KEY,
    SKILL_INTELLIGENCE_KEY,
    SKILL_REGISTRY_KEY,
)

logger = structlog.get_logger()


class SkillRegistryPlugin(HarnessPlugin):
    """Plugin providing SkillRegistryService and SkillGraphService to the micro-kernel."""

    def __init__(self, root_dir: str = ".") -> None:
        self._name = "skill_registry"
        self._version = "0.2.0"
        self._root_dir = root_dir
        self._service: Any = None
        self._graph_service: Any = None
        self._bus: Any = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def _registry(self) -> Any:
        return self._service

    @_registry.setter
    def _registry(self, val: Any) -> None:
        self._service = val

    @property
    def _graph(self) -> Any:
        return self._graph_service

    @_graph.setter
    def _graph(self, val: Any) -> None:
        self._graph_service = val

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [
            SKILL_REGISTRY_KEY,
            SKILL_GRAPH_KEY,
            SKILL_INTELLIGENCE_KEY,
            SKILL_CLUSTERING_KEY,
        ]

    async def on_load(self, context: ServiceContext) -> None:
        from harness.services.skill_graph.service import (
            BuiltinSkillGraphService,
            BuiltinSkillRegistryService,
        )

        self._service = BuiltinSkillRegistryService(default_root=self._root_dir)
        self._graph_service = BuiltinSkillGraphService(registry=self._service)
        context.provide(SKILL_REGISTRY_KEY, self._service, provider=self._name)
        context.provide(SKILL_GRAPH_KEY, self._graph_service, provider=self._name)
        context.provide(SKILL_INTELLIGENCE_KEY, self._service, provider=self._name)
        context.provide(SKILL_CLUSTERING_KEY, self._service, provider=self._name)

        if hasattr(context, "event_bus") and context.event_bus:
            self._bus = context.event_bus
            self._bus.subscribe("file.changed", self._on_skill_file_changed)
            self._bus.subscribe("file.created", self._on_skill_file_changed)

    def _on_skill_file_changed(self, event: Any) -> None:
        """Invalidate the skills cache when a SKILL.md or CARD.md file changes."""
        path = str(getattr(event, "payload", {}).get("path", ""))
        if "SKILL.md" in path or "CARD.md" in path or ".agents/skills" in path:
            if self._service is not None:
                self._service.invalidate_cache()
                logger.info("SkillRegistry cache invalidated due to file change", path=path)

    async def on_enable(self) -> None:
        pass

    async def on_disable(self) -> None:
        pass

    async def on_unload(self) -> None:
        if self._service is not None:
            self._service.invalidate_cache()


__all__ = ["SkillRegistryPlugin"]
