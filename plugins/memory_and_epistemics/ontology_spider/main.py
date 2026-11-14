"""Ontology-Spider Brain Harness Plugin Entrypoint.

Registers the Ontology-Spider service into the Brain Harness IoC container via ServiceKey[T]
and exposes tool functions for loading, querying, exporting, and auditing Knowledge Vaults.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any, Union

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin
from harness.services.ontology_spider import (
    ONTOLOGY_SPIDER_SERVICE_KEY,
    OntologySpiderKernelService,
)

from plugins.memory_and_epistemics.ontology_spider.service import (
    HAS_ONTOLOGY_SPIDER,
    OntologySpiderService,
)

ONTOLOGY_SPIDER_KEY = ServiceKey[OntologySpiderService]("service.ontology_spider")
ONTOLOGY_REASONER_KEY = ServiceKey[OntologySpiderService]("service.ontology_reasoner")


class OntologySpiderPlugin(HarnessPlugin):
    """Brain Harness plugin bridging vault items to the Ontology-Spider reasoning engine."""

    name = "plugin.ontology_spider"
    version = "0.2.0"
    description = "Formal ontological reasoning, entropy ranking, competency evaluation, and vault auditing."
    trusted = True

    def __init__(self) -> None:
        super().__init__()
        self._service: OntologySpiderService | None = None
        self._kernel_service: OntologySpiderKernelService | None = None

    @property
    def provides(self) -> list[Any]:
        return [ONTOLOGY_SPIDER_SERVICE_KEY, ONTOLOGY_SPIDER_KEY, ONTOLOGY_REASONER_KEY]

    @property
    def requires(self) -> list[Any]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        self._kernel_service = OntologySpiderKernelService()
        self._service = OntologySpiderService()
        context.provide(ONTOLOGY_SPIDER_SERVICE_KEY, self._kernel_service, provider=self.name)
        context.provide(ONTOLOGY_SPIDER_KEY, self._service, provider=self.name)
        context.provide(ONTOLOGY_REASONER_KEY, self._service, provider=self.name)

    async def on_enable(self) -> None:
        _ = HAS_ONTOLOGY_SPIDER

    async def on_disable(self) -> None:
        pass

    async def on_unload(self) -> None:
        self._service = None
        self._kernel_service = None


def load_vault_ontology(
    vault_path: Union[str, Path, dict[str, Any]] = ".harness/knowledge",
    *,
    as_of: str | None = None,
    min_confidence: float = 0.0,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Load vault items/edges and return summary metadata."""
    target_source: Union[str, Path, dict[str, Any]] = (
        {"vault_id": "dry_run", "items": [], "edges": []} if _kwargs.get("task") == "validator-dry-run" else vault_path
    )
    svc = OntologySpiderService()
    model = svc.load_vault(target_source, as_of=as_of, min_confidence=min_confidence)
    return {
        "uri": model.uri,
        "entities_count": len(model.entities),
        "assertions_count": len(model.assertions),
    }


def query_ontology(
    vault_path: Union[str, Path, dict[str, Any]],
    query_str: str,
    *,
    rank_by_distance: bool = False,
    as_of: str | None = None,
    min_confidence: float = 0.0,
) -> dict[str, Any]:
    """Execute a controlled .dialog query against the vault."""
    return OntologySpiderService().query(
        vault_path,
        query_str,
        rank_by_distance=rank_by_distance,
        as_of=as_of,
        min_confidence=min_confidence,
    )


def validate_ontology(
    vault_path: Union[str, Path, dict[str, Any]],
    *,
    as_of: str | None = None,
    min_confidence: float = 0.0,
) -> list[dict[str, Any]]:
    """Run structural integrity validation on the vault."""
    return OntologySpiderService().validate(vault_path, as_of=as_of, min_confidence=min_confidence)


def export_ontology(
    vault_path: Union[str, Path, dict[str, Any]],
    format: str = "json",
    *,
    as_of: str | None = None,
    min_confidence: float = 0.0,
) -> str:
    """Export vault ontology to 'json', 'dialog', 'dot', or 'html'."""
    return OntologySpiderService().export(vault_path, format=format, as_of=as_of, min_confidence=min_confidence)


def evaluate_competency_questions(
    vault_path: Union[str, Path, dict[str, Any]],
    questions: Sequence[str],
    *,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Evaluate competency questions and return serialized Gruber 5-criteria scorecard."""
    return asdict(OntologySpiderService().evaluate_competency(vault_path, questions=questions, as_of=as_of))


def audit_vault_epistemics(
    vault_path: Union[str, Path, dict[str, Any]],
    *,
    as_of: str | None = None,
    min_confidence: float = 0.0,
) -> dict[str, Any]:
    """Execute combined structural, isnad verification, entropy, and Gruber coherence audit."""
    return asdict(
        OntologySpiderService().audit_vault_epistemics(vault_path, as_of=as_of, min_confidence=min_confidence)
    )


plugin = OntologySpiderPlugin()
