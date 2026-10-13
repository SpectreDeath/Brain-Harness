"""Decomposition and contract verification tests for EarthEngineImagery subsystem."""

from __future__ import annotations

from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from plugins.geospatial_and_osint.earth_engine_imagery.engine import (
    CompositeResult,
    EARTH_ENGINE_IMAGERY_KEY,
    EarthEngineImageryEngine,
    EarthEngineImageryService,
    ImageDescription,
    ImageSearchMixin,
    SceneMetadata,
    SpectralIndexResult,
    SpectralProcessingMixin,
    TemporalCompositingMixin,
    ThumbnailResult,
    resolve_earth_engine_imagery,
)
from plugins.geospatial_and_osint.earth_engine_imagery.main import (
    EarthEngineImageryPlugin,
    plugin,
)


def test_submodule_line_counts_and_boundaries():
    """Verify all submodules in engine/ and main.py adhere strictly to <= 200 line limit (Rule 11)."""
    pkg_dir = Path("plugins/geospatial_and_osint/earth_engine_imagery")
    py_files = list(pkg_dir.rglob("*.py"))
    assert len(py_files) >= 8

    for py_file in py_files:
        lines = py_file.read_text(encoding="utf-8").splitlines()
        assert len(lines) <= 200, f"{py_file} exceeds 200 lines ({len(lines)})"


def test_slotted_dataclass_invariants():
    """Verify domain models utilize __slots__ per Rules 12 & 43."""
    scene = SceneMetadata(
        id="S2/test",
        date="2026-04-01",
        cloud_cover_percentage=5.0,
        crs="EPSG:32610",
        bands=["B4", "B8"],
    )
    assert hasattr(scene, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        scene.unregistered_dyn_attr = "invalid"

    spec = SpectralIndexResult(
        status="ok",
        mode="simulation",
        image_id="S2/test",
        index_type="NDVI",
        formula="(B8 - B4) / (B8 + B4)",
        output_band="ndvi",
    )
    assert hasattr(spec, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        spec.unregistered_dyn_attr = "invalid"

    comp = CompositeResult(
        status="ok",
        mode="simulation",
        collection_id="S2",
        bbox=[-122.5, 37.7, -122.3, 37.9],
        temporal_window=["2026-01-01", "2026-06-01"],
        composite_method="median",
    )
    assert hasattr(comp, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        comp.unregistered_dyn_attr = "invalid"

    thumb = ThumbnailResult(
        status="ok",
        mode="simulation",
        image_id="S2/test",
        thumbnail_url="http://test.url",
    )
    assert hasattr(thumb, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        thumb.unregistered_dyn_attr = "invalid"

    desc = ImageDescription(
        status="ok",
        mode="simulation",
        image_id="S2/test",
    )
    assert hasattr(desc, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        desc.unregistered_dyn_attr = "invalid"


def test_single_seam_resolver_pattern():
    """Verify single-seam resolver resolve_earth_engine_imagery adheres to Rule 58."""
    # 1. Fallback without context
    svc1 = resolve_earth_engine_imagery(None)
    assert isinstance(svc1, EarthEngineImageryService)

    # 2. Empty context fallback
    ctx = ServiceContext()
    svc2 = resolve_earth_engine_imagery(ctx)
    assert isinstance(svc2, EarthEngineImageryService)

    # 3. Context resolution when plugin provides service
    test_plugin = EarthEngineImageryPlugin()
    ctx.provide(EARTH_ENGINE_IMAGERY_KEY, test_plugin._engine, provider="test")
    resolved = resolve_earth_engine_imagery(ctx)
    assert resolved is test_plugin._engine


def test_composite_engine_mixin_inheritance():
    """Verify EarthEngineImageryEngine cleanly composes search, spectral, and temporal mixins."""
    assert issubclass(EarthEngineImageryEngine, ImageSearchMixin)
    assert issubclass(EarthEngineImageryEngine, SpectralProcessingMixin)
    assert issubclass(EarthEngineImageryEngine, TemporalCompositingMixin)

    engine = EarthEngineImageryEngine()
    assert callable(engine.search_image_collection)
    assert callable(engine.compute_spectral_index)
    assert callable(engine.composite_timeseries)
    assert callable(engine.get_image_thumbnail_url)
    assert callable(engine.describe_image)


def test_plugin_module_singleton_export():
    """Verify main.py exports plugin module singleton per Rule 45."""
    assert isinstance(plugin, EarthEngineImageryPlugin)
    assert plugin.name == "plugin.earth_engine_imagery"
    assert EARTH_ENGINE_IMAGERY_KEY in plugin.provides
