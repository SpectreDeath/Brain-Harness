"""Discovery Index Scout Plugin entrypoint for Brain Harness."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import structlog

# Ensure Harness core src is on sys.path
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.discovery_index import (
    DISCOVERY_INDEX_SERVICE_KEY,
    DiscoveryIndexService,
    DiscoverySearchResult,
    DiscoverySourceModel,
    DiscoveryStatsModel,
    LocalDiscoveryIndexService,
)

logger = structlog.get_logger(__name__)


class DiscoveryIndexScoutPlugin(HarnessPlugin, DiscoveryIndexService):
    """
    Brain Harness Plugin providing in-memory discovery index scouting and catalog queries.
    Elevates .agents/skills/discovery-index-scout into an authoritative IoC micro-kernel seam.
    """

    name = "domain.discovery_index_scout"
    version = "1.0.0"
    description = "Discovery Index Scout engine: multi-domain search across transcripts, public records, research corpora, and open data indexes."
    trusted = True

    def __init__(self) -> None:
        super().__init__()
        workspace_root = Path(__file__).resolve().parents[3]
        self._impl: DiscoveryIndexService = LocalDiscoveryIndexService(workspace_root=workspace_root)

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [DISCOVERY_INDEX_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin", plugin=self.name)
        ctx.provide(DISCOVERY_INDEX_SERVICE_KEY, self, provider=self.name)

    async def on_enable(self) -> None:
        logger.info("enabling_plugin", plugin=self.name)

    async def on_disable(self) -> None:
        logger.info("disabling_plugin", plugin=self.name)

    # --- DiscoveryIndexService Protocol Implementation ---

    async def search(
        self,
        query: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        provenance_tier: str | None = None,
        export_format: str | None = None,
        limit: int = 20,
    ) -> list[DiscoverySearchResult]:
        return await self._impl.search(
            query=query,
            category=category,
            tag=tag,
            provenance_tier=provenance_tier,
            export_format=export_format,
            limit=limit,
        )

    async def get_source(self, source_id: str) -> DiscoverySourceModel | None:
        return await self._impl.get_source(source_id)

    async def list_sources(self, category: str | None = None) -> list[DiscoverySourceModel]:
        return await self._impl.list_sources(category=category)

    async def register_source(self, source_data: dict[str, Any], persist: bool = True) -> DiscoverySourceModel:
        return await self._impl.register_source(source_data, persist=persist)

    async def get_stats(self) -> DiscoveryStatsModel:
        return await self._impl.get_stats()


# Module-level plugin singleton (Rule 45)
plugin = DiscoveryIndexScoutPlugin()


# Top-level tool entrypoints matching plugin.json
async def discovery_search(
    query: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    provenance_tier: str | None = None,
    export_format: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search discovery catalog by query, category, tag, or provenance tier."""
    results = await plugin.search(
        query=query,
        category=category,
        tag=tag,
        provenance_tier=provenance_tier,
        export_format=export_format,
        limit=limit,
    )
    return [r.__dict__ if hasattr(r, "__dict__") else r for r in results]


async def discovery_get_source(source_id: str) -> dict[str, Any] | None:
    """Retrieve details for a single discovery source by ID."""
    source = await plugin.get_source(source_id)
    if source is None:
        return None
    return source.__dict__ if hasattr(source, "__dict__") else source


async def discovery_get_stats() -> dict[str, Any]:
    """Retrieve statistical rollups across the discovery knowledge catalog."""
    stats = await plugin.get_stats()
    return stats.__dict__ if hasattr(stats, "__dict__") else stats

