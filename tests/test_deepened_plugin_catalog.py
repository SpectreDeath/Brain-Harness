"""Unit and integration tests for the deepened PluginCatalog and SandboxedPlugin invocation seam."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from harness.events.bus import EventBus
from harness.events.types import EventType
from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.catalog import PluginCatalog
from harness.plugins.loader import PluginLoader
from harness.plugins.manifest import IsolationMode, PluginManifest
from harness.plugins.sandbox import InProcessExecutor
from harness.plugins.sandboxed import PluginCallResult, SandboxedPlugin


@pytest.fixture
def plugins_dir() -> Path:
    return Path("plugins")


@pytest.fixture
def catalog(plugins_dir: Path) -> PluginCatalog:
    return PluginCatalog(plugin_dirs=[plugins_dir])


@pytest.mark.unit
def test_plugin_catalog_discovery_and_indexing(catalog: PluginCatalog) -> None:
    """Assert that the catalog scans the multi-domain plugins directory and indexes entries."""
    assert len(catalog) > 0

    # Ensure domains were detected
    domains = catalog.domains()
    assert "data_engineering" in domains
    assert "software_engineering" in domains
    assert "agent_orchestration" in domains
    assert "security_and_forensics" in domains

    # Lookup by exact name
    entry = catalog.get("plugin.data_transformer")
    assert entry is not None
    assert entry.name == "plugin.data_transformer"
    assert entry.domain == "data_engineering"
    assert entry.has_manifest is True

    # Lookup by short alias without 'plugin.' prefix
    entry_short = catalog.get("data_transformer")
    assert entry_short is not None
    assert entry_short.name == "plugin.data_transformer"

    # Lookup by path
    entry_by_path = catalog.get(entry.path)
    assert entry_by_path is not None
    assert entry_by_path.name == "plugin.data_transformer"


@pytest.mark.unit
def test_plugin_catalog_filtering(catalog: PluginCatalog) -> None:
    """Assert multi-criteria filtering on the plugin catalog."""
    # Filter by domain
    de_plugins = catalog.filter(domain="data_engineering")
    assert len(de_plugins) >= 3
    assert all(e.domain == "data_engineering" for e in de_plugins)

    # Filter by isolation mode
    in_proc_plugins = catalog.filter(isolation="in_process")
    assert len(in_proc_plugins) > 0
    assert all(e.isolation == "in_process" for e in in_proc_plugins)

    # Filter by trusted flag
    trusted_plugins = catalog.filter(trusted_only=True)
    assert len(trusted_plugins) > 0
    assert all(e.trusted is True for e in trusted_plugins)

    # Filter with non-matching criteria returns empty list
    non_existent = catalog.filter(domain="non_existent_domain_xyz")
    assert non_existent == []


@pytest.mark.unit
def test_plugin_catalog_search(catalog: PluginCatalog) -> None:
    """Assert search ranking across name, description, and capabilities."""
    # Search by capability keyword
    results = catalog.search("transformer")
    assert len(results) > 0
    assert any("transformer" in e.name.lower() for e in results)

    # Search by category keyword
    results_sql = catalog.search("database")
    assert len(results_sql) > 0

    # Search with empty query returns all
    all_entries = catalog.search("")
    assert len(all_entries) == len(catalog)


@pytest.mark.unit
def test_plugin_catalog_manifest_and_guide_caching(catalog: PluginCatalog) -> None:
    """Assert zero-cost cached manifest and guide generation."""
    entry = catalog.get("plugin.data_transformer")
    assert entry is not None

    # First call loads manifest
    manifest1 = entry.get_manifest()
    assert manifest1 is not None
    assert manifest1.name == "plugin.data_transformer"

    # Second call returns cached manifest
    manifest2 = entry.get_manifest()
    assert manifest1 is manifest2

    # Guide generation
    guide = entry.get_guide()
    assert "data_transformer" in guide
    assert entry.get_guide() == guide

    # Test catalog helper get_guide
    res = catalog.get_guide("plugin.data_transformer")
    assert res is not None
    m, g = res
    assert m.name == "plugin.data_transformer"
    assert "data_transformer" in g


@pytest.mark.unit
def test_plugin_loader_catalog_delegation(plugins_dir: Path) -> None:
    """Assert PluginLoader transparently delegates catalog queries to PluginCatalog."""
    loader = PluginLoader(plugin_dirs=[plugins_dir])

    # Direct catalog access
    assert isinstance(loader.catalog, PluginCatalog)
    assert len(loader.catalog) > 0

    # Delegated list_catalog
    raw_catalog = loader.list_catalog()
    assert isinstance(raw_catalog, list)
    assert len(raw_catalog) > 0
    first_item = raw_catalog[0]
    assert "name" in first_item
    assert "domain" in first_item
    assert "path" in first_item

    # Delegated find_plugin_dir
    pdir = loader.find_plugin_dir("data_transformer")
    assert pdir is not None
    assert pdir.exists()

    # Delegated get_manifest and get_guide
    m = loader.get_manifest("data_transformer")
    assert m is not None
    assert m.name == "plugin.data_transformer"

    g = loader.get_guide("data_transformer")
    assert g is not None
    assert g[0].name == "plugin.data_transformer"


@pytest.mark.asyncio
async def test_sandboxed_plugin_typed_invocation_ok(tmp_path: Path) -> None:
    """Assert SandboxedPlugin.invoke_typed executes successfully and records telemetry."""
    manifest = PluginManifest(
        name="test_plugin",
        version="1.0.0",
        isolation=IsolationMode.IN_PROCESS,
        trusted=True,
    )

    class DummyModule:
        async def add(self, a: int, b: int) -> int:
            return a + b

    executor = InProcessExecutor(DummyModule())
    plugin = SandboxedPlugin(manifest=manifest, root=tmp_path, executor=executor)

    ctx = ServiceContext()
    await plugin.on_load(ctx)
    await plugin.on_enable()

    # Execute typed invocation
    result: PluginCallResult = await plugin.invoke_typed("add", {"a": 10, "b": 25})
    assert result.is_ok is True
    assert result.is_error is False
    assert result.result == 35
    assert result.latency_ms >= 0.0
    assert result.method == "add"
    assert result.plugin == "test_plugin"
    assert result.correlation_id is not None

    # Verify metrics updated
    metrics = plugin.get_metrics()
    assert metrics["invocations"] == 1
    assert metrics["errors"] == 0

    # Backward compatible dict call
    dict_res = await plugin.call("add", {"a": 2, "b": 3})
    assert dict_res["status"] == "ok"
    assert dict_res["result"] == 5

    await plugin.on_disable()
    await plugin.on_unload()


@pytest.mark.asyncio
async def test_sandboxed_plugin_typed_invocation_error_handling(tmp_path: Path) -> None:
    """Assert SandboxedPlugin handles missing methods and emits failure events."""
    manifest = PluginManifest(
        name="error_plugin",
        version="1.0.0",
        isolation=IsolationMode.IN_PROCESS,
        trusted=True,
    )

    class DummyModule:
        def crash(self) -> None:
            raise ValueError("Intentional crash")

    executor = InProcessExecutor(DummyModule())
    plugin = SandboxedPlugin(manifest=manifest, root=tmp_path, executor=executor)

    # Set up context with EventBus for telemetry capture
    event_bus = EventBus()
    ctx = ServiceContext()
    ctx.provide(ServiceKey("events.bus"), event_bus)

    await plugin.on_load(ctx)
    await plugin.on_enable()

    captured_events: list[Any] = []

    async def _on_error(evt: Any) -> None:
        captured_events.append(evt)

    event_bus.on(EventType.PLUGIN_ERROR, _on_error)

    # 1. Method not found
    res_not_found = await plugin.invoke_typed("non_existent_method")
    assert res_not_found.is_error is True
    assert res_not_found.error_code == "NOT_FOUND"

    # Verify event published in event bus log
    plugin_error_events = [e for e in event_bus.log if e.event_type == EventType.PLUGIN_ERROR]
    assert len(plugin_error_events) >= 1
    assert plugin_error_events[0].payload["plugin"] == "error_plugin"
    assert plugin_error_events[0].payload["method"] == "non_existent_method"

    # 2. Execution failure
    res_crash = await plugin.invoke_typed("crash")
    assert res_crash.is_error is True
    assert "Intentional crash" in (res_crash.error or "")

    metrics = plugin.get_metrics()
    assert metrics["errors"] == 2

    await plugin.on_disable()
    await plugin.on_unload()
