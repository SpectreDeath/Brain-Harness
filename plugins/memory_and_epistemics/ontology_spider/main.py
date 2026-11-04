"""Main plugin entrypoint and HarnessPlugin lifecycle integration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Union

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

from .service import OntologySpiderService

logger = logging.getLogger(__name__)

ONTOLOGY_SPIDER_KEY = ServiceKey[OntologySpiderService]("service.ontology_spider")
ONTOLOGY_REASONER_KEY = ServiceKey[OntologySpiderService]("service.ontology_reasoner")


class OntologySpiderPlugin(HarnessPlugin):
    """Domain-partitioned plugin integrating Ontology-Spider formal logic reasoning into Brain Harness."""

    name = "plugin.ontology_spider"
    version = "0.2.0"
    description = "Formal logic reasoning, multi-hop dependency traversal, and schema validation over Brain Harness vaults"
    author = "Brain Harness Epistemics Engine"

    def __init__(self) -> None:
        super().__init__()
        self._service = OntologySpiderService()

    @property
    def provides(self) -> list[Any]:
        return [ONTOLOGY_SPIDER_KEY, ONTOLOGY_REASONER_KEY]

    @property
    def requires(self) -> list[Any]:
        return []

    async def on_load(self, ctx: ServiceContext) -> None:
        logger.info("loading_plugin: %s", self.name)
        ctx.provide(ONTOLOGY_SPIDER_KEY, self._service)
        ctx.provide(ONTOLOGY_REASONER_KEY, self._service)

    async def on_enable(self) -> None:
        logger.info("enabled_plugin: %s", self.name)

    async def on_disable(self) -> None:
        logger.info("disabled_plugin: %s", self.name)

    async def on_unload(self) -> None:
        logger.info("unloaded_plugin: %s", self.name)


# Global singleton instance
plugin = OntologySpiderPlugin()
_service_instance = plugin._service


# Standalone entrypoint helpers callable via JSON-RPC or direct Python invocation
def load_vault_ontology(vault_source: Union[str, Path, dict[str, Any]]) -> dict[str, Any]:
    """Load a vault into an OntologyModel and return its serialized summary."""
    model = _service_instance.load_vault(vault_source)
    return {
        "uri": model.uri,
        "entities_count": len(model.entities),
        "assertions_count": len(model.assertions),
    }


def query_ontology(vault_source: Union[str, Path, dict[str, Any]], query: str) -> dict[str, Any]:
    """Execute a query against a vault model, returning answers and proof trace."""
    return _service_instance.query(vault_source, query)


def validate_ontology(vault_source: Union[str, Path, dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate a vault ontology, returning schema violations."""
    return _service_instance.validate(vault_source)
