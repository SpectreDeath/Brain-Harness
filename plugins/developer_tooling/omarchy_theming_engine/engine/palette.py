"""TOML colors parsing, legacy alias resolution, and palette derivation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

from .color import ColorRGB, mix_colors

# TOML parsing with fallback
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]

logger = structlog.get_logger(__name__)


def parse_colors_file(file_path: Path) -> dict[str, str]:
    """Parse TOML colors file with fallback key-value parser."""
    data: dict[str, Any] = {}
    try:
        with open(file_path, "rb") as f:
            if tomllib is not None:
                data = tomllib.load(f)
    except Exception:
        pass

    if not data:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        key = k.strip().strip("'\"")
                        val = v.split("#")[0].strip().strip("'\"")
                        data[key] = val
        except Exception as exc:
            logger.warning("omarchy_colors_parse_failed", file=str(file_path), error=str(exc))

    flat: dict[str, str] = {}
    for k, v in data.items():
        if isinstance(v, dict):
            for sub_k, sub_v in v.items():
                flat[f"{k}_{sub_k}"] = str(sub_v)
        else:
            flat[k] = str(v)
    return flat


def resolve_palette(raw: dict[str, str], theme_dir: Path) -> dict[str, str]:
    """Mirror the full alias and derivation pipeline from omarchy-theme-color."""
    colors = dict(raw)

    # 1. Legacy palette aliases
    legacy_palette_alias = {
        "background": "bg",
        "dark_background": "dark_bg",
        "darker_background": "darker_bg",
        "lighter_background": "lighter_bg",
        "foreground": "fg",
        "dark_foreground": "dark_fg",
        "light_foreground": "light_fg",
        "bright_foreground": "bright_fg",
    }
    for full, short in legacy_palette_alias.items():
        if full not in colors and short in colors:
            colors[full] = colors[short]

    # 2. ANSI fallback for bg/fg
    if "background" not in colors and "color0" in colors:
        colors["background"] = colors["color0"]
    if "foreground" not in colors and "color7" in colors:
        colors["foreground"] = colors["color7"]
    if "background" in colors and "color0" not in colors:
        colors["color0"] = colors["background"]
    if "foreground" in colors and "color7" not in colors:
        colors["color7"] = colors["foreground"]

    if "background" not in colors:
        colors["background"] = "#1e1e2e"
    if "foreground" not in colors:
        colors["foreground"] = "#cdd6f4"

    # 3. ANSI to semantic mapping
    legacy_ansi = {
        "red": "color1",
        "green": "color2",
        "yellow": "color3",
        "blue": "color4",
        "magenta": "color5",
        "cyan": "color6",
        "bright_red": "color9",
        "bright_green": "color10",
        "bright_yellow": "color11",
        "bright_blue": "color12",
        "bright_magenta": "color13",
        "bright_cyan": "color14",
    }
    for sem, ansi in legacy_ansi.items():
        if sem not in colors and ansi in colors:
            colors[sem] = colors[ansi]

    if "magenta" not in colors and "purple" in colors:
        colors["magenta"] = colors["purple"]
    if "bright_magenta" not in colors and "bright_purple" in colors:
        colors["bright_magenta"] = colors["bright_purple"]

    # Semantic defaults
    colors["light_foreground"] = colors.get("light_foreground") or colors.get("color7") or colors["foreground"]
    colors["bright_foreground"] = colors.get("bright_foreground") or colors.get("color15") or colors["foreground"]
    colors["cursor"] = colors.get("cursor") or colors["bright_foreground"]
    colors["lighter_background"] = colors.get("lighter_background") or colors.get("color0") or colors["background"]
    colors["dark_foreground"] = colors.get("dark_foreground") or colors.get("color8") or colors["foreground"]
    colors["muted"] = colors.get("muted") or colors.get("color8") or colors["dark_foreground"]
    colors["selection"] = (
        colors.get("selection")
        or colors.get("selection_background")
        or colors.get("color8")
        or colors["background"]
    )
    colors["selection_background"] = colors.get("selection_background") or colors["selection"]
    colors["selection_foreground"] = colors.get("selection_foreground") or colors["bright_foreground"]
    colors["orange"] = colors.get("orange") or colors.get("yellow") or "#f6b6ab"
    colors["brown"] = colors.get("brown") or mix_colors(colors["orange"], "#000000", 0.50)

    # 4. Auto-derive shades if missing
    if "dark_background" not in colors:
        colors["dark_background"] = mix_colors(colors["background"], "#000000", 0.25)
    if "darker_background" not in colors:
        colors["darker_background"] = mix_colors(colors["background"], "#000000", 0.50)

    for base_color in ["red", "yellow", "green", "cyan", "blue", "magenta"]:
        bright_key = f"bright_{base_color}"
        if bright_key not in colors and base_color in colors:
            colors[bright_key] = mix_colors(colors[base_color], "#ffffff", 0.20)

    colors["purple"] = colors.get("purple") or colors.get("magenta", "#f5c2e7")
    colors["bright_purple"] = colors.get("bright_purple") or colors.get("bright_magenta", "#f5c2e7")

    # 5. Populate ANSI aliases backwards for template consumers
    ansi_backwards = {
        "color0": colors["background"],
        "color1": colors.get("red", "#f38ba8"),
        "color2": colors.get("green", "#a6e3a1"),
        "color3": colors.get("yellow", "#f9e2af"),
        "color4": colors.get("blue", "#89b4fa"),
        "color5": colors.get("magenta", "#f5c2e7"),
        "color6": colors.get("cyan", "#94e2d5"),
        "color7": colors["foreground"],
        "color8": colors["muted"],
        "color9": colors.get("bright_red", colors.get("red", "#f38ba8")),
        "color10": colors.get("bright_green", colors.get("green", "#a6e3a1")),
        "color11": colors.get("bright_yellow", colors.get("yellow", "#f9e2af")),
        "color12": colors.get("bright_blue", colors.get("blue", "#89b4fa")),
        "color13": colors.get("bright_magenta", colors.get("magenta", "#f5c2e7")),
        "color14": colors.get("bright_cyan", colors.get("cyan", "#94e2d5")),
        "color15": colors["bright_foreground"],
    }
    for k, v in ansi_backwards.items():
        if k not in colors:
            colors[k] = v

    if "accent" not in colors:
        colors["accent"] = colors.get("blue", "#89b4fa")

    # 6. Mode resolution
    if "mode" not in colors:
        if "theme_type" in colors:
            colors["mode"] = colors["theme_type"]
        elif (theme_dir / "light.mode").exists():
            colors["mode"] = "light"
        else:
            bg = ColorRGB.from_hex(colors["background"])
            lum_sum = bg.r + bg.g + bg.b
            colors["mode"] = "light" if lum_sum > 382 else "dark"

    return colors
