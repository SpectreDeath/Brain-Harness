"""Service layer executing logic reasoning and validation over vault ontologies."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Union

try:
    from ontology_spider.api import export_model, run_query, validate_model
    from ontology_spider.model import OntologyModel
    HAS_ONTOLOGY_SPIDER = True
except ModuleNotFoundError:
    HAS_ONTOLOGY_SPIDER = False
    export_model = None  # type: ignore
    run_query = None  # type: ignore
    validate_model = None  # type: ignore
    OntologyModel = Any  # type: ignore

from .adapter import HarnessVaultModelSource


class OntologySpiderService:
    """Core service for loading, querying, validating, and explaining vault models."""

    @staticmethod
    def _assert_engine() -> None:
        if not HAS_ONTOLOGY_SPIDER:
            raise RuntimeError(
                "The 'ontology_spider' engine is not installed. "
                "Install it via: pip install -e <path-to-Ontology-Spider> "
                "or consult plugins/memory_and_epistemics/ontology_spider/README.md"
            )

    def load_vault(self, source: Union[str, Path, dict[str, Any]]) -> Any:
        """Load an OntologyModel from a vault source using the seam adapter."""
        self._assert_engine()
        adapter = HarnessVaultModelSource(source)
        return adapter.load()

    def query(self, source: Union[str, Path, dict[str, Any]], query_str: str) -> dict[str, Any]:
        """Execute a query against a vault model, returning answers and full proof explanations."""
        self._assert_engine()
        model = self.load_vault(source)
        return run_query(model, query_str)

    def validate(self, source: Union[str, Path, dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate schema integrity and constraints across the vault ontology."""
        self._assert_engine()
        model = self.load_vault(source)
        return validate_model(model)

    def export(self, source: Union[str, Path, dict[str, Any]], fmt: str = "json") -> str:
        """Export a vault ontology to a specified representation (json, dialog, dot, html)."""
        self._assert_engine()
        model = self.load_vault(source)
        return export_model(model, fmt)
