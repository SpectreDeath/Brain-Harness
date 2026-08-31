"""Unit tests for Kimi MiniDb Plugin and Storage Engine."""

import pytest
from pathlib import Path

from harness.creator.validator import PluginValidator
from harness.kernel.context import ServiceContext
from harness.services.kimi_bridge import (
    KIMI_MINIDB_KEY,
    KimiMiniDbService,
    MiniDbRecord,
)
from plugins.data_engineering.kimi_minidb.main import (
    KimiMiniDbPlugin,
    MiniDbEngine,
    kimi_minidb_put,
    kimi_minidb_get,
    kimi_minidb_compact,
)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_plugin_manifest_validation() -> None:
    """Validate that plugin.kimi_minidb manifest passes all PluginValidator checks."""
    plugin_dir = Path("plugins/data_engineering/kimi_minidb")
    assert plugin_dir.exists(), "Plugin directory must exist"

    report = await PluginValidator.validate(plugin_dir)
    assert report.valid, f"Plugin manifest validation failed: {report.errors}"
    assert len(report.errors) == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_plugin_lifecycle_and_service_registration() -> None:
    """Test enabling KimiMiniDbPlugin registers KIMI_MINIDB_KEY into context."""
    context = ServiceContext()
    plugin = KimiMiniDbPlugin()

    await plugin.on_enable(context)
    assert context.has(KIMI_MINIDB_KEY)

    service = context.require(KIMI_MINIDB_KEY)
    assert service is not None
    assert isinstance(service, KimiMiniDbService)

    await plugin.on_disable(context)


@pytest.mark.unit
def test_minidb_put_get_and_crc32() -> None:
    """Test inserting and retrieving documents with CRC32 checksum verification."""
    engine = MiniDbEngine()

    rec = engine.put("users", "u101", {"name": "Alice", "role": "admin"})
    assert isinstance(rec, MiniDbRecord)
    assert rec.key == "u101"
    assert rec.collection == "users"
    assert rec.crc32_checksum > 0
    assert rec.wal_sequence == 1
    assert rec.generation == 1

    fetched = engine.get("users", "u101")
    assert fetched is not None
    assert fetched.value == {"name": "Alice", "role": "admin"}
    assert fetched.crc32_checksum == rec.crc32_checksum

    # Missing record returns None
    missing = engine.get("users", "nonexistent")
    assert missing is None


@pytest.mark.unit
def test_minidb_scan_and_filter() -> None:
    """Test collection scan and custom filtering."""
    engine = MiniDbEngine()

    for i in range(10):
        engine.put("items", f"item_{i}", {"val": i, "even": (i % 2 == 0)})

    all_items = engine.scan("items")
    assert len(all_items) == 10

    even_items = engine.scan("items", filter_fn=lambda r: r.value.get("even") is True)
    assert len(even_items) == 5


@pytest.mark.unit
def test_minidb_generational_compaction() -> None:
    """Test snapshot compaction merges WAL frames and increments generation."""
    engine = MiniDbEngine()

    for i in range(15):
        engine.put("cache", f"key_{i}", {"data": i * 10})

    assert len(engine._wal_log) == 15
    assert engine._generation == 1

    report = engine.compact()
    assert report["status"] == "ok"
    assert report["new_generation"] == 2
    assert report["wal_frames_reclaimed"] == 15
    assert report["total_records_preserved"] == 15
    assert len(engine._wal_log) == 0

    # Ensure records are still retrievable with updated generation
    rec = engine.get("cache", "key_5")
    assert rec is not None
    assert rec.generation == 2
    assert rec.value == {"data": 50}


@pytest.mark.asyncio
@pytest.mark.unit
async def test_minidb_async_tools() -> None:
    """Test top-level async tool entrypoints."""
    put_res = await kimi_minidb_put(collection="audit", key="tx_01", value={"status": "committed"})
    assert put_res["status"] == "ok"
    assert put_res["record"]["key"] == "tx_01"

    get_res = await kimi_minidb_get(collection="audit", key="tx_01")
    assert get_res["status"] == "ok"
    assert get_res["record"]["value"] == {"status": "committed"}

    compact_res = await kimi_minidb_compact()
    assert compact_res["status"] == "ok"
