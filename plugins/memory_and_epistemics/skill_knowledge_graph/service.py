"""SkillGraphPlugin implementation providing graph, registry, clustering, and intelligence services."""

from __future__ import annotations

from typing import Any

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.plugins.tool_mount import ToolMountMixin
from harness.services.skill_clustering import SKILL_CLUSTERING_KEY
from harness.services.skill_graph import (
    SKILL_GRAPH_KEY,
    SKILL_INTELLIGENCE_KEY,
    SKILL_REGISTRY_KEY,
    get_default_skill_registry,
)
from harness.services.tools import TOOL_REGISTRY_KEY, ToolSpec

from .graph import SkillKnowledgeGraph
from .mixins import (
    ClusteringServiceMixin,
    GraphServiceMixin,
    IntelligenceServiceMixin,
    RegistryServiceMixin,
)
from .tools import (
    cluster_skill_graph,
    discover_emergent_capabilities,
    get_skill_topology,
    index_skill_catalog,
    invalidate_skill_catalog,
    select_skills_for_task,
)


class SkillGraphPlugin(
    ToolMountMixin,
    HarnessPlugin,
    GraphServiceMixin,
    RegistryServiceMixin,
    ClusteringServiceMixin,
    IntelligenceServiceMixin,
):
    """In-process Harness plugin providing SkillGraphService, SkillRegistryService, and SkillClusteringService."""

    name = "plugin.skill_knowledge_graph"
    version = "1.0.0"
    description = "Knowledge graph indexer, semantic router, cluster capability discovery, and skill selector"
    trusted = True

    def __init__(self) -> None:
        self._registry = get_default_skill_registry()
        self._graph = SkillKnowledgeGraph(registry=self._registry)

    def _get_registry(self) -> Any:
        return self._registry

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [
            SKILL_GRAPH_KEY,
            SKILL_REGISTRY_KEY,
            SKILL_CLUSTERING_KEY,
            SKILL_INTELLIGENCE_KEY,
        ]

    async def on_load(self, ctx: ServiceContext) -> None:
        ctx.provide(SKILL_GRAPH_KEY, self, allow_override=True)
        ctx.provide(SKILL_REGISTRY_KEY, self._registry, allow_override=True)
        ctx.provide(SKILL_CLUSTERING_KEY, self._registry, allow_override=True)
        ctx.provide(SKILL_INTELLIGENCE_KEY, self._registry, allow_override=True)
        self.setup_tool_mount(ctx, self.name)

        if hasattr(self._registry, "add_invalidation_listener"):
            self._registry.add_invalidation_listener(invalidate_skill_catalog)

        try:
            from harness.events.bus import EVENT_BUS_KEY
            from harness.events.types import EventType

            bus = ctx.optional(EVENT_BUS_KEY)
            if bus:
                ctx.subscribe(EventType.FILE_MODIFIED, self._on_skill_file_changed)
                ctx.subscribe(EventType.FILE_CREATED, self._on_skill_file_changed)
                ctx.subscribe(EventType.FILE_DELETED, self._on_skill_file_changed)
        except Exception:
            pass

    def _on_skill_file_changed(self, event: Any) -> None:
        """Handle EventBus file change events by invalidating graph and registry caches."""
        payload = getattr(event, "payload", {}) or {}
        path = str(payload.get("path", ""))
        if "SKILL.md" in path or "CARD.md" in path:
            invalidate_skill_catalog()

    async def on_enable(self) -> None:
        index_skill_catalog(".")
        if self._mount_ctx and self._mount_ctx.has(TOOL_REGISTRY_KEY):
            tools = [
                ToolSpec(
                    name="select_skills",
                    description=(
                        "Intelligently select agent skills and compile a prerequisite-aware "
                        "topological execution plan for a given task using the skill knowledge graph."
                    ),
                    executor=lambda task, max_skills=5, include_verifier=True: (
                        select_skills_for_task(
                            task,
                            max_skills=max_skills,
                            include_verifier=include_verifier,
                        )
                    ),
                ),
                ToolSpec(
                    name="cluster_skills",
                    description=(
                        "Cluster workspace skills into cohesive capability domains and uncover "
                        "emergent macro-capabilities."
                    ),
                    executor=lambda min_cluster_size=2, min_size=None, **kwargs: (
                        cluster_skill_graph(
                            min_cluster_size=min_size
                            if min_size is not None
                            else min_cluster_size
                        )
                    ),
                ),
                ToolSpec(
                    name="discover_capabilities",
                    description=(
                        "Search novel emergent capabilities formed by composite multi-skill "
                        "pipelines in the knowledge graph."
                    ),
                    executor=lambda query="": discover_emergent_capabilities(
                        query=query or None
                    ),
                ),
                ToolSpec(
                    name="get_skill_topology",
                    description=(
                        "Retrieve upstream prerequisites, downstream handoffs, invariants, and "
                        "mitigated anti-patterns for a given skill."
                    ),
                    executor=lambda skill_name: get_skill_topology(skill_name),
                ),
            ]
            await self.mount_tools(tools)

    async def on_disable(self) -> None:
        await self.unmount_tools()

    async def on_unload(self) -> None:
        pass
