"""Brain Harness Service wrapping Ontology-Spider query, validation, export, and audit."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any, Union

from harness.services.ontology_spider import (
    HAS_ONTOLOGY_SPIDER,
    AttributeEntropyRank,
    CompetencyScorecardReport,
    EpistemicVaultAuditReport,
    OntologySpiderKernelService,
)

__all__ = ["HAS_ONTOLOGY_SPIDER", "OntologySpiderService"]


class OntologySpiderService:
    """Programmatic and tool service binding Harness Knowledge Vaults to Ontology-Spider."""

    def __init__(self) -> None:
        self._kernel = OntologySpiderKernelService()

    def load_vault(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        *,
        as_of: str | None = None,
        min_confidence: float = 0.0,
    ) -> Any:
        """Load a Knowledge Vault JSON, directory, or dict into an OntologyModel."""
        return self._kernel.load_vault(vault_source, as_of=as_of, min_confidence=min_confidence)

    def query(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        query_str: str,
        *,
        rank_by_distance: bool = False,
        as_of: str | None = None,
        min_confidence: float = 0.0,
        max_results: int | None = 5000,
    ) -> dict[str, Any]:
        """Run a controlled .dialog query against the vault model and return JSON-serializable results."""
        return self._kernel.query(
            vault_source,
            query_str,
            rank_by_distance=rank_by_distance,
            as_of=as_of,
            min_confidence=min_confidence,
            max_results=max_results,
        )

    def validate(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        *,
        as_of: str | None = None,
        min_confidence: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Validate schema integrity (cycles, disjointness, domain/range) for the vault."""
        return self._kernel.validate(vault_source, as_of=as_of, min_confidence=min_confidence)

    def export(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        format: str = "json",
        *,
        as_of: str | None = None,
        min_confidence: float = 0.0,
    ) -> str:
        """Export vault ontology to 'json', 'dialog', 'dot', or 'html'."""
        return self._kernel.export(vault_source, format=format, as_of=as_of, min_confidence=min_confidence)

    def rank_attributes(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        candidate_ids: Sequence[str] | None = None,
        *,
        as_of: str | None = None,
    ) -> tuple[AttributeEntropyRank, ...]:
        """Rank vault entity attributes by Shannon/Laya expected information gain."""
        return self._kernel.rank_attributes(vault_source, candidate_ids=candidate_ids, as_of=as_of)

    def evaluate_competency(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        questions: Sequence[str],
        *,
        as_of: str | None = None,
    ) -> CompetencyScorecardReport:
        """Evaluate .dialog competency questions and compute Gruber 5-criteria scorecard."""
        return self._kernel.evaluate_competency(vault_source, questions=questions, as_of=as_of)

    def audit_vault_epistemics(
        self,
        vault_source: Union[str, Path, dict[str, Any]],
        *,
        as_of: str | None = None,
        min_confidence: float = 0.0,
    ) -> EpistemicVaultAuditReport:
        """Run combined structural, isnad verification, entropy, and Gruber coherence audit."""
        return self._kernel.audit_vault_epistemics(vault_source, as_of=as_of, min_confidence=min_confidence)
