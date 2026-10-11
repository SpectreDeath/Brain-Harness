"""Authoritative catalog and deterministic router coordinator for 14 open-source GIS engines."""

from __future__ import annotations

from pathlib import Path

from harness.services.open_source_gis.catalog.fallback import get_fallback_engine_catalog
from harness.services.open_source_gis.catalog.loader import (
    find_resource_file,
    load_default_catalog,
    load_default_weights,
)
from harness.services.open_source_gis.catalog.router import route_workload as _route_workload
from harness.services.open_source_gis.models import (
    EngineSelectionResult,
    GISEngineRecord,
    SpatialWorkloadProfile,
)


class GISEngineCatalog:
    """Authoritative catalog and deterministic router for 14 open-source GIS engines."""

    def __init__(self, engines: list[GISEngineRecord] | None = None) -> None:
        if engines is None:
            self.engines = self._load_default_catalog()
        else:
            self.engines = engines
        self._by_name = {e.name: e for e in self.engines}
        self._default_weights = self._load_default_weights()

    @classmethod
    def _find_resource_file(cls, filename: str) -> Path | None:
        """Locate catalog or config file across workspace roots."""
        return find_resource_file(filename)

    @classmethod
    def _load_default_catalog(cls) -> list[GISEngineRecord]:
        return load_default_catalog()

    @classmethod
    def _load_default_weights(cls) -> dict[str, float]:
        return load_default_weights()

    @classmethod
    def _fallback_engine_catalog(cls) -> list[GISEngineRecord]:
        return get_fallback_engine_catalog()

    def get_engine(self, name: str) -> GISEngineRecord | None:
        return self._by_name.get(name)

    def route_workload(
        self, profile: SpatialWorkloadProfile, weights: dict[str, float] | None = None
    ) -> EngineSelectionResult:
        """Route workload to optimal primary and secondary GIS engines using deterministic paths."""
        return _route_workload(self._by_name, profile, weights=weights or self._default_weights)
