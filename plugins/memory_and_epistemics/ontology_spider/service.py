"""Service layer executing logic reasoning and validation over vault ontologies."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Union

from ontology_spider.api import export_model, run_query, validate_model
from ontology_spider.model import OntologyModel

from .adapter import HarnessVaultModelSource


class OntologySpiderService:
    """Core service for loading, querying, validating, and explaining vault models."""

    def load_vault(self, source: Union[str, Path, dict[str, Any]]) -> OntologyModel:
        """Load an OntologyModel from a vault source using the seam adapter."""
        adapter = HarnessVaultModelSource(source)
        return adapter.load()

    def query(self, source: Union[str, Path, dict[str, Any]], query_str: str) -> dict[str, Any]:
        """Execute a query against a vault model, returning answers and full proof explanations."""
        model = self.load_vault(source)
        return run_query(model, query_str)

    def validate(self, source: Union[str, Path, dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate schema integrity and constraints across the vault ontology."""
        model = self.load_vault(source)
        return validate_model(model)

    def export(self, source: Union[str, Path, dict[str, Any]], fmt: str = "json") -> str:
        """Export a vault ontology to a specified representation (json, dialog, dot, html)."""
        model = self.load_vault(source)
        return export_model(model, fmt)
