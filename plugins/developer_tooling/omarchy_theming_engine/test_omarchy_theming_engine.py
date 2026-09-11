"""Tests for Omarchy Theming Engine Plugin."""

from pathlib import Path
import pytest
import sys

# Ensure Harness core is on path
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

from harness.kernel.context import ServiceContext
from plugins.developer_tooling.omarchy_theming_engine.main import (
    ColorRGB,
    mix_colors,
    compute_contrast_ratio,
    OmarchyThemingEngineServiceImpl,
    OmarchyThemingEnginePlugin,
    OMARCHY_THEMING_ENGINE_SERVICE_KEY,
    omarchy_list_themes,
    omarchy_get_theme_palette,
    omarchy_render_theme_template,
    omarchy_validate_theme_contrast,
    plugin,
)


def test_color_rgb_and_mix() -> None:
    c1 = ColorRGB.from_hex("#000000")
    assert c1.r == 0 and c1.g == 0 and c1.b == 0
    assert c1.to_rgb_str() == "0,0,0"

    c2 = ColorRGB.from_hex("#ffffff")
    assert c2.r == 255 and c2.g == 255 and c2.b == 255

    # 50% mix between black and white
    mixed = mix_colors("#000000", "#ffffff", "50%")
    # 0.5 * 255 = 127.5 -> 128 (0x80)
    assert mixed == "#808080"

    # Contrast ratio between black and white should be 21:1
    contrast = compute_contrast_ratio("#000000", "#ffffff")
    assert contrast >= 20.0


@pytest.fixture
def mock_theme_dir(tmp_path: Path) -> Path:
    themes_dir = tmp_path / "themes"
    themes_dir.mkdir()

    # Theme 1: catppuccin mock with semantic names
    theme1 = themes_dir / "test-dark"
    theme1.mkdir()
    (theme1 / "colors.toml").write_text(
        'mode = "dark"\n'
        'background = "#1e1e2e"\n'
        'foreground = "#cdd6f4"\n'
        'accent = "#89b4fa"\n'
        'red = "#f38ba8"\n'
        'green = "#a6e3a1"\n'
        'yellow = "#f9e2af"\n'
        'blue = "#89b4fa"\n',
        encoding="utf-8",
    )

    # Theme 2: legacy ANSI theme with short names (bg/fg)
    theme2 = themes_dir / "test-legacy"
    theme2.mkdir()
    (theme2 / "colors.toml").write_text(
        'bg = "#101010"\n'
        'fg = "#eeeeee"\n'
        'color1 = "#ff0000"\n'
        'color2 = "#00ff00"\n',
        encoding="utf-8",
    )

    return tmp_path


def test_theming_engine_list_and_palette(mock_theme_dir: Path) -> None:
    service = OmarchyThemingEngineServiceImpl(source_dir=mock_theme_dir)
    themes = service.list_themes()
    assert len(themes) == 2

    # Verify test-dark
    palette_dark = service.get_theme_palette("test-dark")
    assert palette_dark["background"] == "#1e1e2e"
    assert palette_dark["foreground"] == "#cdd6f4"
    assert palette_dark["mode"] == "dark"
    # Auto-derived dark_background
    assert "dark_background" in palette_dark
    assert palette_dark["dark_background"].startswith("#")

    # Verify test-legacy alias resolution
    palette_legacy = service.get_theme_palette("test-legacy")
    assert palette_legacy["background"] == "#101010"
    assert palette_legacy["foreground"] == "#eeeeee"
    assert palette_legacy["red"] == "#ff0000"
    assert palette_legacy["green"] == "#00ff00"


def test_theming_engine_template_rendering(mock_theme_dir: Path) -> None:
    service = OmarchyThemingEngineServiceImpl(source_dir=mock_theme_dir)

    template = (
        "bg_hex = '{{ background }}'\n"
        "bg_strip = '{{ background_strip }}'\n"
        "bg_rgb = '{{ background_rgb }}'\n"
        "mixed = '{{ mix background foreground 50% }}'\n"
        "mixed_strip = '{{ mix_strip background foreground 50% }}'\n"
        "mixed_rgb = '{{ mix_rgb background foreground 50% }}'\n"
    )

    rendered = service.render_theme_template(template, "test-dark")
    assert "bg_hex = '#1e1e2e'" in rendered
    assert "bg_strip = '1e1e2e'" in rendered
    assert "bg_rgb = '30,30,46'" in rendered
    assert "mixed = '#" in rendered
    assert "mixed_strip = '" in rendered
    assert "mixed_rgb = '" in rendered
    # Ensure no raw templates remain
    assert "{{" not in rendered


def test_theming_engine_contrast_validation(mock_theme_dir: Path) -> None:
    service = OmarchyThemingEngineServiceImpl(source_dir=mock_theme_dir)
    report = service.validate_theme_contrast("test-dark")

    assert report["theme_name"] == "test-dark"
    assert report["mode"] == "dark"
    assert "foreground_on_background" in report["checks"]
    check = report["checks"]["foreground_on_background"]
    assert check["ratio"] > 4.5
    assert check["passes_wcag_aa"] is True


@pytest.mark.asyncio
async def test_theming_engine_plugin_lifecycle() -> None:
    context = ServiceContext()
    p = OmarchyThemingEnginePlugin()

    await p.enable(context)
    resolved = context.require(OMARCHY_THEMING_ENGINE_SERVICE_KEY)
    assert resolved is not None
    assert hasattr(resolved, "list_themes")
    assert hasattr(resolved, "get_theme_palette")
    assert hasattr(resolved, "render_theme_template")
    assert hasattr(resolved, "validate_theme_contrast")

    await p.disable(context)


def test_real_omarchy_themes_if_available() -> None:
    real_path = Path(r"D:\GitHub\cloned\omarchy-quattro\omarchy-quattro")
    if not real_path.exists():
        pytest.skip("Real Omarchy checkout not found")

    service = OmarchyThemingEngineServiceImpl(source_dir=real_path)
    themes = service.list_themes()
    assert len(themes) >= 20

    # Test catppuccin palette
    catppuccin = service.get_theme_palette("catppuccin")
    assert catppuccin["background"] == "#1e1e2e"
    assert catppuccin["accent"] == "#89b4fa"

    # Test contrast
    contrast = service.validate_theme_contrast("catppuccin")
    assert contrast["checks"]["foreground_on_background"]["passes_wcag_aa"] is True
