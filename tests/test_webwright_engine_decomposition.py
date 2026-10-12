"""Decomposition and contract verification tests for WebwrightHarnessEngine subsystem."""

from __future__ import annotations

import inspect
from pathlib import Path
import pytest

from harness.kernel.context import ServiceContext
from harness.services.webwright_harness import WEBWRIGHT_HARNESS_KEY
from plugins.integration_and_io.webwright_harness import (
    WebwrightHarnessEngine,
    WebwrightHarnessPlugin,
)
from plugins.integration_and_io.webwright_harness.engine import (
    BrowserDaemonMixin,
    BrowserDaemonState,
    ReflectionMixin,
    SkillLearningMixin,
    SkillMetadata,
    SkillRetrievalMixin,
    SkillRoutingMixin,
    resolve_webwright_engine,
)
from plugins.integration_and_io.webwright_harness.main import plugin


def test_submodule_line_counts_and_boundaries():
    """Verify all submodules in engine/ and main.py adhere strictly to <= 200 line limit (Rule 11)."""
    engine_dir = Path("plugins/integration_and_io/webwright_harness/engine")
    py_files = list(engine_dir.glob("*.py"))
    assert len(py_files) >= 7

    for py_file in py_files:
        lines = py_file.read_text(encoding="utf-8").splitlines()
        assert len(lines) <= 200, f"{py_file} exceeds 200 lines ({len(lines)})"

    main_lines = Path("plugins/integration_and_io/webwright_harness/main.py").read_text(encoding="utf-8").splitlines()
    assert len(main_lines) <= 200, f"main.py exceeds 200 lines ({len(main_lines)})"


def test_slotted_dataclass_invariants():
    """Verify SkillMetadata and BrowserDaemonState utilize __slots__ per Rules 12 & 43."""
    meta = SkillMetadata(
        skill_id="test_skill",
        template="click {btn}",
        summary="Test skill summary",
        signature={"params": ["btn"]},
        output_schema={"type": "object"},
        file_path="skills/test_skill/skill.py",
        created_at=1234567.0,
    )
    assert hasattr(meta, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        meta.unregistered_dyn_attr = "invalid"

    daemon = BrowserDaemonState(pid=1234, port=9222)
    assert hasattr(daemon, "__slots__")
    with pytest.raises((AttributeError, TypeError)):
        daemon.unregistered_dyn_attr = "invalid"


def test_single_seam_resolver_pattern():
    """Verify single-seam resolver resolve_webwright_engine adheres to Rule 58."""
    # 1. Fallback without context
    eng1 = resolve_webwright_engine(None)
    assert isinstance(eng1, WebwrightHarnessEngine)

    # 2. Empty context fallback
    ctx = ServiceContext()
    eng2 = resolve_webwright_engine(ctx)
    assert isinstance(eng2, WebwrightHarnessEngine)

    # 3. Context resolution when plugin provides service
    test_plugin = WebwrightHarnessPlugin()
    ctx.provide(WEBWRIGHT_HARNESS_KEY, test_plugin, provider="test")
    resolved = resolve_webwright_engine(ctx)
    assert resolved is test_plugin._engine


def test_composite_engine_mixin_inheritance():
    """Verify WebwrightHarnessEngine cleanly composes all 5 specialized mixins."""
    assert issubclass(WebwrightHarnessEngine, SkillLearningMixin)
    assert issubclass(WebwrightHarnessEngine, SkillRetrievalMixin)
    assert issubclass(WebwrightHarnessEngine, SkillRoutingMixin)
    assert issubclass(WebwrightHarnessEngine, BrowserDaemonMixin)
    assert issubclass(WebwrightHarnessEngine, ReflectionMixin)

    engine = WebwrightHarnessEngine()
    assert callable(engine.learn_skill)
    assert callable(engine.retrieve_skills)
    assert callable(engine.route_and_execute)
    assert callable(engine.manage_browser_session)
    assert callable(engine.image_qa)
    assert callable(engine.self_reflect)


def test_plugin_module_singleton_export():
    """Verify main.py exports plugin module singleton per Rule 45."""
    assert isinstance(plugin, WebwrightHarnessPlugin)
    assert plugin.name == "plugin.webwright_harness"
    assert WEBWRIGHT_HARNESS_KEY in plugin.provides
