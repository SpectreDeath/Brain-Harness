"""Discovery Index Service protocol, slotted/frozen models, engine, and ServiceKey."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import structlog

from harness.kernel.context import ServiceKey

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Slotted & Frozen Domain Models (Rule 12)
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class DiscoverySourceModel:
    """Immutable metadata describing a discovered primary source or research repository."""

    id: str
    name: str
    category: str
    url: str
    description: str
    access_method: str
    provenance_tier: str
    update_cadence: str = "Continuous / As Published"
    export_formats: tuple[str, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""
    added_at: str = ""

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("DiscoverySourceModel.name cannot be empty")
        if not self.url or not self.url.strip():
            raise ValueError("DiscoverySourceModel.url cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "url": self.url,
            "description": self.description,
            "access_method": self.access_method,
            "provenance_tier": self.provenance_tier,
            "update_cadence": self.update_cadence,
            "export_formats": list(self.export_formats),
            "tags": list(self.tags),
            "notes": self.notes,
            "added_at": self.added_at,
        }


@dataclass(slots=True, frozen=True)
class DiscoverySearchResult:
    """Immutable search match result with relevance scoring and matched fields."""

    source: DiscoverySourceModel
    relevance_score: float
    matched_fields: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        data = self.source.to_dict()
        data["relevance_score"] = round(self.relevance_score, 2)
        data["matched_fields"] = list(self.matched_fields)
        return data


@dataclass(slots=True, frozen=True)
class DiscoveryStatsModel:
    """Faceted distribution statistics across categories and provenance tiers."""

    total_sources: int
    by_category: dict[str, int] = field(default_factory=dict)
    by_provenance: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_sources": self.total_sources,
            "by_category": dict(self.by_category),
            "by_provenance": dict(self.by_provenance),
        }


# ---------------------------------------------------------------------------
# Service Protocol & ServiceKey (Rule 2 & Rule 49)
# ---------------------------------------------------------------------------


@runtime_checkable
class DiscoveryIndexService(Protocol):
    """Authoritative service protocol for discovery index querying and registration."""

    async def search(
        self,
        query: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        provenance_tier: str | None = None,
        export_format: str | None = None,
        limit: int = 20,
    ) -> list[DiscoverySearchResult]:
        """Execute weighted multi-field search with faceted filtering."""
        ...

    async def get_source(self, source_id: str) -> DiscoverySourceModel | None:
        """Retrieve source by exact identifier."""
        ...

    async def list_sources(self, category: str | None = None) -> list[DiscoverySourceModel]:
        """List all registered discovery sources, optionally filtered by category."""
        ...

    async def register_source(self, source_data: dict[str, Any], persist: bool = True) -> DiscoverySourceModel:
        """Register or update a discovery source endpoint."""
        ...

    async def get_stats(self) -> DiscoveryStatsModel:
        """Compute faceted distribution statistics."""
        ...


DISCOVERY_INDEX_SERVICE_KEY: ServiceKey[DiscoveryIndexService] = ServiceKey("service.discovery_index")


# ---------------------------------------------------------------------------
# Default In-Memory Implementation
# ---------------------------------------------------------------------------


class LocalDiscoveryIndexService(DiscoveryIndexService):
    """In-memory service implementation delegating to the slotted DiscoveryCatalogEngine."""

    def __init__(self, workspace_root: Path | str | None = None) -> None:
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        skill_scripts_dir = self.workspace_root / ".agents" / "skills" / "discovery-index-scout" / "scripts"

        if not skill_scripts_dir.exists():
            # Fallback path if running from tests or nested dirs
            skill_scripts_dir = Path(__file__).resolve().parents[3] / ".agents" / "skills" / "discovery-index-scout" / "scripts"

        import sys
        if str(skill_scripts_dir) not in sys.path:
            sys.path.insert(0, str(skill_scripts_dir))

        try:
            from discovery_engine import DiscoveryCatalogEngine
            self._engine = DiscoveryCatalogEngine(
                registry_path=skill_scripts_dir.parent / "registry.json",
                config_path=skill_scripts_dir.parent / "config.default.yaml",
            )
        except ImportError:
            logger.warning("discovery_engine could not be imported directly; using standalone fallback")
            self._engine = None  # type: ignore

    def _convert_source(self, src: Any) -> DiscoverySourceModel:
        return DiscoverySourceModel(
            id=src.id,
            name=src.name,
            category=src.category,
            url=src.url,
            description=src.description,
            access_method=src.access_method,
            provenance_tier=src.provenance_tier,
            update_cadence=src.update_cadence,
            export_formats=tuple(src.export_formats),
            tags=tuple(src.tags),
            notes=src.notes,
            added_at=src.added_at,
        )

    async def search(
        self,
        query: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        provenance_tier: str | None = None,
        export_format: str | None = None,
        limit: int = 20,
    ) -> list[DiscoverySearchResult]:
        if not self._engine:
            return []
        results = self._engine.search(
            query=query,
            category=category,
            tag=tag,
            provenance_tier=provenance_tier,
            export_format=export_format,
            limit=limit,
        )
        return [
            DiscoverySearchResult(
                source=self._convert_source(r.source),
                relevance_score=r.score,
                matched_fields=r.matched_fields,
            )
            for r in results
        ]

    async def get_source(self, source_id: str) -> DiscoverySourceModel | None:
        if not self._engine:
            return None
        src = self._engine.get_source(source_id)
        return self._convert_source(src) if src else None

    async def list_sources(self, category: str | None = None) -> list[DiscoverySourceModel]:
        if not self._engine:
            return []
        sources = self._engine.list_all_sources()
        if category:
            sources = [s for s in sources if s.category.lower() == category.lower()]
        return [self._convert_source(s) for s in sources]

    async def register_source(self, source_data: dict[str, Any], persist: bool = True) -> DiscoverySourceModel:
        if not self._engine:
            raise RuntimeError("Discovery engine not initialized")
        src = self._engine.register_source(source_data, persist=persist)
        return self._convert_source(src)

    async def get_stats(self) -> DiscoveryStatsModel:
        if not self._engine:
            return DiscoveryStatsModel(total_sources=0)
        st = self._engine.get_stats()
        return DiscoveryStatsModel(
            total_sources=st.get("total_sources", 0),
            by_category=dict(st.get("by_category", {})),
            by_provenance=dict(st.get("by_provenance", {})),
        )
