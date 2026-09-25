"""Unit test suite for discovery-index-scout deepened domain engine, service protocol, and IoC plugin."""

import asyncio
import json
import sys
import pytest
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / ".agents" / "skills" / "discovery-index-scout" / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from harness.kernel.context import ServiceContext
from harness.services.discovery_index import (
    DISCOVERY_INDEX_SERVICE_KEY,
    DiscoveryIndexService,
    DiscoverySearchResult,
    DiscoverySourceModel,
    DiscoveryStatsModel,
    LocalDiscoveryIndexService,
)

# Import engine directly from skill scripts
from discovery_engine import (
    CURATED_SOURCES_DATA,
    DiscoveryCatalogEngine,
    DiscoverySource,
    SearchResult,
)



@pytest.fixture
def workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def engine() -> DiscoveryCatalogEngine:
    return DiscoveryCatalogEngine()


# ============================================================================
# 1. Slotted & Frozen Model Invariants (Rule 12 & Rule 43)
# ============================================================================

def test_discovery_source_model_immutability():
    """Verify that DiscoverySourceModel is slotted and frozen."""
    src = DiscoverySourceModel(
        id="test-source",
        name="Test Source",
        category="transcripts",
        url="https://example.gov",
        description="A test source",
        access_method="REST API",
        provenance_tier="Primary Official",
    )
    assert src.name == "Test Source"

    # Frozen attribute mutation assertion (Rule 43)
    with pytest.raises((AttributeError, TypeError)):
        src.name = "Mutated Name"  # type: ignore


def test_discovery_source_model_validation():
    """Verify post-init validation rejects empty names or URLs."""
    with pytest.raises(ValueError, match="name cannot be empty"):
        DiscoverySourceModel(
            id="bad-1",
            name="",
            category="transcripts",
            url="https://example.gov",
            description="",
            access_method="",
            provenance_tier="",
        )

    with pytest.raises(ValueError, match="url cannot be empty"):
        DiscoverySourceModel(
            id="bad-2",
            name="Valid Name",
            category="transcripts",
            url="",
            description="",
            access_method="",
            provenance_tier="",
        )


# ============================================================================
# 2. Authoritative Catalog Engine Tests
# ============================================================================

def test_engine_initialization(engine: DiscoveryCatalogEngine):
    """Verify engine loads all 46 curated base sources."""
    sources = engine.list_all_sources()
    assert len(sources) >= 46

    # Verify key known sources exist
    cspan = engine.get_source("c-span-video-library")
    assert cspan is not None
    assert cspan.category == "transcripts"
    assert cspan.provenance_tier == "Primary Official"

    sec = engine.get_source("sec-edgar")
    assert sec is not None
    assert sec.category == "public_records"
    assert "10-k" in sec.tags or "sec" in sec.tags


def test_engine_weighted_ranking(engine: DiscoveryCatalogEngine):
    """Verify weighted search assigns higher relevance to exact title and tag matches."""
    # Searching for 'SEC' should rank 'SEC EDGAR' top
    results = engine.search(query="SEC", limit=5)
    assert len(results) > 0
    top = results[0]
    assert top.source.id == "sec-edgar"
    assert top.score >= 10.0
    assert "title" in top.matched_fields or "title_exact" in top.matched_fields


def test_engine_faceted_filtering(engine: DiscoveryCatalogEngine):
    """Verify faceted filters strictly gate search candidates."""
    # Filter by category
    transcripts = engine.search(category="transcripts", limit=100)
    assert all(r.source.category == "transcripts" for r in transcripts)
    assert len(transcripts) >= 13

    # Filter by provenance tier
    primary_official = engine.search(provenance_tier="Primary Official", limit=100)
    assert all("primary official" in r.source.provenance_tier.lower() for r in primary_official)
    assert len(primary_official) >= 10

    # Filter by export format
    parquet_sources = engine.search(export_format="Parquet", limit=100)
    assert len(parquet_sources) > 0
    assert all(any("parquet" in f.lower() for f in r.source.export_formats) for r in parquet_sources)


def test_engine_source_registration(tmp_path: Path):
    """Verify dynamic source registration and registry persistence."""
    registry_file = tmp_path / "custom_registry.json"
    custom_engine = DiscoveryCatalogEngine(registry_path=registry_file)

    new_source = {
        "id": "state-records",
        "name": "State Open Records",
        "category": "public_records",
        "url": "https://state.example.gov/records",
        "access_method": "CKAN API",
        "provenance_tier": "State Official",
        "export_formats": ["JSON", "CSV"],
        "tags": ["state", "records"],
    }
    src = custom_engine.register_source(new_source, persist=True)
    assert src.id == "state-records"

    # Verify search finds the new source
    matches = custom_engine.search(query="State Open Records")
    assert any(m.source.id == "state-records" for m in matches)

    # Verify persistence to custom file
    assert registry_file.exists()
    saved_data = json.loads(registry_file.read_text(encoding="utf-8"))
    assert any(s["id"] == "state-records" for s in saved_data["sources"])


def test_engine_formatters(engine: DiscoveryCatalogEngine):
    """Verify JSON, Table, and Markdown serialization formatters."""
    results = engine.search(query="presidential", limit=2)
    assert len(results) > 0

    json_str = engine.format_json(results)
    parsed = json.loads(json_str)
    assert parsed["total"] == len(results)
    assert len(parsed["results"]) == len(results)

    table_str = engine.format_table(results)
    assert "SOURCE NAME" in table_str
    assert "CATEGORY" in table_str

    md_str = engine.format_markdown(results)
    assert "| Source | Category |" in md_str


def test_engine_stats(engine: DiscoveryCatalogEngine):
    """Verify stats returns accurate faceted count breakdowns."""
    stats = engine.get_stats()
    assert stats["total_sources"] >= 46
    assert "transcripts" in stats["by_category"]
    assert "public_records" in stats["by_category"]
    assert "research_corpora" in stats["by_category"]
    assert "github_indexes" in stats["by_category"]


# ============================================================================
# 3. Micro-Kernel IoC Service Seam Tests (Rule 49 & Rule 2)
# ============================================================================

@pytest.mark.asyncio
async def test_ioc_service_protocol_adherence(workspace_root: Path):
    """Verify LocalDiscoveryIndexService implements DiscoveryIndexService protocol."""
    service = LocalDiscoveryIndexService(workspace_root=workspace_root)
    assert isinstance(service, DiscoveryIndexService)

    # Test search via async service method
    results = await service.search(query="lobbying", limit=5)
    assert len(results) > 0
    assert any("opensecrets" in r.source.id or "senate" in r.source.id for r in results)

    # Test get_source
    src = await service.get_source("sec-edgar")
    assert src is not None
    assert src.name == "SEC EDGAR"

    # Test get_stats
    stats = await service.get_stats()
    assert stats.total_sources >= 46
    assert isinstance(stats, DiscoveryStatsModel)


@pytest.mark.asyncio
async def test_ioc_service_registration_and_resolution(workspace_root: Path):
    """Verify registration and resolution in ServiceContext via DISCOVERY_INDEX_SERVICE_KEY."""
    ctx = ServiceContext()
    service = LocalDiscoveryIndexService(workspace_root=workspace_root)

    # Provide service (Rule 2)
    ctx.provide(DISCOVERY_INDEX_SERVICE_KEY, service, provider="test")

    # Resolve service
    resolved = ctx.require(DISCOVERY_INDEX_SERVICE_KEY)
    assert resolved is service

    results = await resolved.search(category="research_corpora", limit=3)
    assert len(results) == 3
    assert all(r.source.category == "research_corpora" for r in results)


# ============================================================================
# 4. Plugin Singleton & Lifecycle Tests (Rule 45)
# ============================================================================

@pytest.mark.asyncio
async def test_plugin_singleton_and_lifecycle():
    """Verify DiscoveryIndexScoutPlugin registration in ServiceContext."""
    from plugins.data_engineering.discovery_index_scout.main import plugin

    assert plugin.name == "domain.discovery_index_scout"
    assert DISCOVERY_INDEX_SERVICE_KEY in plugin.provides

    ctx = ServiceContext()
    await plugin.on_load(ctx)

    # Verify service provided
    resolved = ctx.require(DISCOVERY_INDEX_SERVICE_KEY)
    assert resolved is plugin

    stats = await resolved.get_stats()
    assert stats.total_sources >= 46
