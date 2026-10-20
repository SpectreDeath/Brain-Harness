"""Contract and invariant verification for Omarchy Theming Engine decomposition per AGENTS.md Rules 11, 12, 43, 45, and 58."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.kernel.context import ServiceContext
from plugins.developer_tooling.omarchy_theming_engine.engine import (
    DEFAULT_OMARCHY_PATH,
    OMARCHY_THEMING_ENGINE_SERVICE_KEY,
    ColorRGB,
    OmarchyThemingEngineService,
    OmarchyThemingEngineServiceImpl,
    audit_theme_contrast,
    compute_contrast_ratio,
    mix_colors,
    omarchy_get_theme_palette,
    omarchy_list_themes,
    omarchy_render_theme_template,
    omarchy_validate_theme_contrast,
    parse_colors_file,
    render_template,
    resolve_omarchy_theming_engine,
    resolve_palette,
)
from plugins.developer_tooling.omarchy_theming_engine.main import (
    OmarchyThemingEnginePlugin,
    plugin,
)


def test_omarchy_subpackage_line_bounds() -> None:
    """Enforce Rule 11: All files in omarchy_theming_engine must be strictly < 200 lines."""
    base_dir = Path(__file__).resolve().parent.parent / "plugins" / "developer_tooling" / "omarchy_theming_engine"
    engine_dir = base_dir / "engine"
    assert engine_dir.is_dir()

    for p in list(base_dir.glob("*.py")) + list(engine_dir.glob("*.py")):
        line_count = len(p.read_text(encoding="utf-8").splitlines())
        assert (
            line_count < 200
        ), f"File {p.name} has {line_count} lines, exceeding 200 line limit!"


def test_omarchy_subpackage_exports() -> None:
    """Verify all symbols are cleanly exported from engine and main facades."""
    assert issubclass(ColorRGB, object)
    assert OMARCHY_THEMING_ENGINE_SERVICE_KEY.name == "service.omarchy_theming_engine"
    assert callable(mix_colors)
    assert callable(compute_contrast_ratio)
    assert callable(resolve_omarchy_theming_engine)
    assert callable(render_template)
    assert callable(audit_theme_contrast)
    assert callable(omarchy_list_themes)
    assert callable(omarchy_get_theme_palette)
    assert callable(omarchy_render_theme_template)
    assert callable(omarchy_validate_theme_contrast)


def test_slotted_frozen_dataclass_immutability() -> None:
    """Enforce Rule 12 & Rule 43: ColorRGB must be slotted and frozen."""
    c = ColorRGB(10, 20, 30)
    assert c.r == 10
    assert c.g == 20
    assert c.b == 30
    assert c.to_hex() == "#0a141e"
    assert c.to_rgb_str() == "10,20,30"

    with pytest.raises((AttributeError, TypeError)):
        c.r = 99  # type: ignore[misc]

    assert hasattr(c, "__slots__")


def test_single_seam_resolver_contract() -> None:
    """Enforce Rule 58: resolve_omarchy_theming_engine across targets."""
    # 1. Target is None -> new default instance
    engine1 = resolve_omarchy_theming_engine()
    assert isinstance(engine1, OmarchyThemingEngineService)

    # 2. Target is existing engine -> returns identity
    assert resolve_omarchy_theming_engine(engine1) is engine1

    # 3. Target is ServiceContext -> resolves or registers onto OMARCHY_THEMING_ENGINE_SERVICE_KEY
    context = ServiceContext()
    assert context.optional(OMARCHY_THEMING_ENGINE_SERVICE_KEY) is None
    engine2 = resolve_omarchy_theming_engine(context)
    assert isinstance(engine2, OmarchyThemingEngineService)
    assert context.optional(OMARCHY_THEMING_ENGINE_SERVICE_KEY) is engine2

    # Idempotent re-resolution
    engine3 = resolve_omarchy_theming_engine(context)
    assert engine3 is engine2


def test_module_level_singleton_invariant() -> None:
    """Enforce Rule 45: main.py must export plugin singleton."""
    assert isinstance(plugin, OmarchyThemingEnginePlugin)
    assert OMARCHY_THEMING_ENGINE_SERVICE_KEY in plugin.provides
    assert plugin.name == "plugin.omarchy_theming_engine"


def test_renderer_and_accessibility_logic() -> None:
    """Verify template rendering and WCAG contrast auditing in isolation."""
    palette = {
        "background": "#000000",
        "foreground": "#ffffff",
        "dark_background": "#111111",
        "dark_foreground": "#888888",
        "light_foreground": "#cccccc",
        "bright_foreground": "#ffffff",
        "accent": "#58a6ff",
        "selection": "#333333",
        "selection_foreground": "#ffffff",
        "mode": "dark",
    }

    # Test template rendering
    tmpl = "bg: {{ background }}, fg_strip: {{ foreground_strip }}, mix: {{ mix background foreground 50% }}"
    rendered = render_template(tmpl, palette)
    assert "bg: #000000" in rendered
    assert "fg_strip: ffffff" in rendered
    assert "mix: #808080" in rendered

    # Test WCAG contrast audit
    audit = audit_theme_contrast(palette, "test-theme")
    assert audit["theme_name"] == "test-theme"
    assert audit["mode"] == "dark"
    assert audit["checks"]["foreground_on_background"]["passes_wcag_aaa"] is True
    assert audit["checks"]["foreground_on_background"]["ratio"] == 21.0
