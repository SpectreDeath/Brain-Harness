"""Omarchy Quattro Theming Engine & Template Renderer Plugin.

Provides TOML palette parsing, legacy alias resolution, sed-compatible template
interpolation, mix/gradient evaluations, and WCAG 2.1 accessibility auditing.
"""

from __future__ import annotations

import math
import os
import re
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
import structlog

# Ensure Harness core src is on sys.path for isolated subprocesses
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

if __name__ not in sys.modules:
    sys.modules[__name__] = sys.modules.get("__main__") or types.ModuleType(__name__)

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

# TOML parsing with fallback
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]

logger = structlog.get_logger(__name__)

DEFAULT_OMARCHY_PATH = Path(r"D:\GitHub\cloned\omarchy-quattro\omarchy-quattro")


@dataclass(slots=True, frozen=True)
class ColorRGB:
    """Slotted immutable representation of 8-bit sRGB color (Rule 12)."""

    r: int
    g: int
    b: int

    @classmethod
    def from_hex(cls, hex_str: str) -> ColorRGB:
        clean = hex_str.strip().lstrip("#")
        if len(clean) == 3:
            clean = "".join(c * 2 for c in clean)
        if len(clean) < 6:
            return cls(0, 0, 0)
        try:
            return cls(
                r=int(clean[0:2], 16),
                g=int(clean[2:4], 16),
                b=int(clean[4:6], 16),
            )
        except ValueError:
            return cls(0, 0, 0)

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def to_rgb_str(self) -> str:
        return f"{self.r},{self.g},{self.b}"

    def relative_luminance(self) -> float:
        """Compute WCAG 2.1 relative luminance."""
        def channel_lum(val: int) -> float:
            c = val / 255.0
            return c / 12.92 if c <= 0.04045 else math.pow((c + 0.055) / 1.055, 2.4)

        return (
            0.2126 * channel_lum(self.r)
            + 0.7152 * channel_lum(self.g)
            + 0.0722 * channel_lum(self.b)
        )


def mix_colors(start_hex: str, end_hex: str, amount: float | str) -> str:
    """Interpolate two hex colors linearly, exactly matching Omarchy's awk algorithm."""
    start = ColorRGB.from_hex(start_hex)
    end = ColorRGB.from_hex(end_hex)

    if isinstance(amount, str):
        amt_clean = amount.strip()
        if amt_clean.endswith("%"):
            pct = float(amt_clean[:-1]) / 100.0
        else:
            pct = float(amt_clean)
            if pct > 1.0:
                pct = pct / 100.0
    else:
        pct = float(amount)
        if pct > 1.0:
            pct = pct / 100.0

    pct = max(0.0, min(1.0, pct))

    # Match awk: int(start * (1 - amount) + end * amount + 0.5)
    red = int(start.r * (1.0 - pct) + end.r * pct + 0.5)
    green = int(start.g * (1.0 - pct) + end.g * pct + 0.5)
    blue = int(start.b * (1.0 - pct) + end.b * pct + 0.5)

    red = max(0, min(255, red))
    green = max(0, min(255, green))
    blue = max(0, min(255, blue))

    return f"#{red:02x}{green:02x}{blue:02x}"


def compute_contrast_ratio(hex_a: str, hex_b: str) -> float:
    """Compute WCAG 2.1 contrast ratio between two colors."""
    lum_a = ColorRGB.from_hex(hex_a).relative_luminance()
    lum_b = ColorRGB.from_hex(hex_b).relative_luminance()
    l1 = max(lum_a, lum_b)
    l2 = min(lum_a, lum_b)
    return round((l1 + 0.05) / (l2 + 0.05), 2)


@runtime_checkable
class OmarchyThemingEngineService(Protocol):
    """Protocol for Omarchy Theme management, palette extraction, and template rendering."""

    def list_themes(self, **kwargs: Any) -> list[dict[str, Any]]:
        ...

    def get_theme_palette(self, theme_name: str, **kwargs: Any) -> dict[str, Any]:
        ...

    def render_theme_template(
        self,
        template_content: str,
        theme_name: str,
        **kwargs: Any,
    ) -> str:
        ...

    def validate_theme_contrast(self, theme_name: str, **kwargs: Any) -> dict[str, Any]:
        ...


OMARCHY_THEMING_ENGINE_SERVICE_KEY = ServiceKey[OmarchyThemingEngineService](
    "service.omarchy_theming_engine"
)


class OmarchyThemingEngineServiceImpl:
    """Implementation of Omarchy Theming Engine service."""

    def __init__(self, source_dir: Path | str | None = None) -> None:
        self._source_dir_override = Path(source_dir) if source_dir else None
        self._palette_cache: dict[str, dict[str, str]] = {}

    @property
    def source_dir(self) -> Path:
        if self._source_dir_override:
            return self._source_dir_override
        env_path = os.environ.get("OMARCHY_PATH")
        if env_path:
            return Path(env_path)
        return DEFAULT_OMARCHY_PATH

    @property
    def themes_dir(self) -> Path:
        return self.source_dir / "themes"

    def list_themes(self, **kwargs: Any) -> list[dict[str, Any]]:
        """List all available Omarchy themes with color highlights."""
        themes_path = self.themes_dir
        if not themes_path.exists() or not themes_path.is_dir():
            logger.warning("omarchy_themes_dir_not_found", path=str(themes_path))
            return []

        themes_list = []
        for entry in sorted(themes_path.iterdir()):
            if not entry.is_dir():
                continue

            palette = self.get_theme_palette(entry.name)
            if "error" in palette:
                continue

            themes_list.append({
                "name": entry.name,
                "mode": palette.get("mode", "dark"),
                "background": palette.get("background", "#000000"),
                "foreground": palette.get("foreground", "#ffffff"),
                "accent": palette.get("accent", palette.get("blue", "#0000ff")),
                "selection": palette.get("selection", "#333333"),
                "has_colors_toml": (entry / "colors.toml").exists(),
            })

        return themes_list

    def get_theme_palette(self, theme_name: str, **kwargs: Any) -> dict[str, Any]:
        """Load and resolve full semantic and ANSI color palette for a theme."""
        clean_theme = theme_name.strip()
        if clean_theme in self._palette_cache:
            return dict(self._palette_cache[clean_theme])

        theme_path = self.themes_dir / clean_theme
        if not theme_path.exists():
            return {
                "error": f"Theme '{clean_theme}' not found in {self.themes_dir}",
                "theme_name": clean_theme,
            }

        colors_file = theme_path / "colors.toml"
        if not colors_file.exists():
            # Check for alternative theme.toml
            colors_file = theme_path / "theme.toml"

        raw_colors: dict[str, str] = {}
        if colors_file.exists():
            raw_colors = self._parse_colors_file(colors_file)

        resolved = self._resolve_palette(raw_colors, theme_path)
        self._palette_cache[clean_theme] = resolved
        return dict(resolved)

    def _parse_colors_file(self, file_path: Path) -> dict[str, str]:
        """Parse TOML colors file with fallback key-value parser."""
        data: dict[str, Any] = {}
        try:
            with open(file_path, "rb") as f:
                if tomllib is not None:
                    data = tomllib.load(f)
        except Exception:
            pass

        if not data:
            # Fallback simple key-value parser
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

        # Flatten any nested tables
        flat: dict[str, str] = {}
        for k, v in data.items():
            if isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    flat[f"{k}_{sub_k}"] = str(sub_v)
            else:
                flat[k] = str(v)
        return flat

    def _resolve_palette(self, raw: dict[str, str], theme_dir: Path) -> dict[str, str]:
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

        # Default fallbacks if neither defined
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

        # Accent default
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

    def render_theme_template(
        self,
        template_content: str,
        theme_name: str,
        **kwargs: Any,
    ) -> str:
        """Render template with {{ key }}, {{ key_strip }}, {{ key_rgb }}, and {{ mix ... }}."""
        palette = self.get_theme_palette(theme_name)
        if "error" in palette:
            raise ValueError(f"Cannot render template: {palette['error']}")

        rendered = template_content

        # 1. Process mix functions first:
        # {{ mix start end amount }}
        # {{ mix_strip start end amount }}
        # {{ mix_rgb start end amount }}
        mix_pattern = re.compile(
            r"\{\{\s*mix(_strip|_rgb)?\s+([A-Za-z0-9_]+)\s+([A-Za-z0-9_]+)\s+([0-9]+(?:\.[0-9]+)?%?)\s*\}\}"
        )

        def replace_mix(match: re.Match[str]) -> str:
            variant = match.group(1) or ""
            start_key = match.group(2)
            end_key = match.group(3)
            amount = match.group(4)

            start_col = palette.get(start_key, "#000000")
            end_col = palette.get(end_key, "#ffffff")
            mixed_hex = mix_colors(start_col, end_col, amount)

            if variant == "_strip":
                return mixed_hex.lstrip("#")
            elif variant == "_rgb":
                return ColorRGB.from_hex(mixed_hex).to_rgb_str()
            return mixed_hex

        rendered = mix_pattern.sub(replace_mix, rendered)

        # 2. Process gradient functions:
        # {{ hypr_gradient key fallback }}
        # {{ gradient_start key fallback }}
        # {{ shell_gradient key fallback }}
        grad_pattern = re.compile(
            r"\{\{\s*(hypr_gradient|gradient_start|shell_gradient)\s+([A-Za-z0-9_]+)(?:\s+([A-Za-z0-9_#]+))?\s*\}\}"
        )

        def replace_gradient(match: re.Match[str]) -> str:
            fn = match.group(1)
            key = match.group(2)
            fallback = match.group(3) or ""
            val = palette.get(key, palette.get(fallback, fallback or key))

            if fn == "gradient_start":
                # First color token
                parts = val.split()
                first = parts[0] if parts else val
                return palette.get(first, first)
            elif fn == "shell_gradient":
                return val
            elif fn == "hypr_gradient":
                parts = [p for p in val.split() if p]
                colors = [palette.get(p, p) for p in parts if not p.endswith("deg")]
                angle = next((p.replace("deg", "") for p in parts if p.endswith("deg")), "")
                if len(colors) <= 1:
                    c = colors[0] if colors else val
                    return f'"{c}"'
                col_str = ", ".join(f'"{c}"' for c in colors)
                if angle:
                    return f"{{ colors = {{ {col_str} }}, angle = {angle} }}"
                return f"{{ colors = {{ {col_str} }} }}"
            return val

        rendered = grad_pattern.sub(replace_gradient, rendered)

        # 3. Process key_strip: {{ key_strip }}
        strip_pattern = re.compile(r"\{\{\s*([A-Za-z0-9_]+)_strip\s*\}\}")

        def replace_strip(match: re.Match[str]) -> str:
            k = match.group(1)
            if k in palette:
                return palette[k].lstrip("#")
            return match.group(0)

        rendered = strip_pattern.sub(replace_strip, rendered)

        # 4. Process key_rgb: {{ key_rgb }}
        rgb_pattern = re.compile(r"\{\{\s*([A-Za-z0-9_]+)_rgb\s*\}\}")

        def replace_rgb(match: re.Match[str]) -> str:
            k = match.group(1)
            if k in palette:
                return ColorRGB.from_hex(palette[k]).to_rgb_str()
            return match.group(0)

        rendered = rgb_pattern.sub(replace_rgb, rendered)

        # 5. Process standard key: {{ key }}
        val_pattern = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")

        def replace_val(match: re.Match[str]) -> str:
            k = match.group(1)
            if k in palette:
                return palette[k]
            return match.group(0)

        rendered = val_pattern.sub(replace_val, rendered)

        return rendered

    def validate_theme_contrast(self, theme_name: str, **kwargs: Any) -> dict[str, Any]:
        """Analyze WCAG 2.1 contrast ratios and accessibility metrics for a theme."""
        palette = self.get_theme_palette(theme_name)
        if "error" in palette:
            return palette

        bg = palette.get("background", "#000000")
        dark_bg = palette.get("dark_background", "#000000")
        selection = palette.get("selection", "#333333")

        checks = {
            "foreground_on_background": {
                "text": palette.get("foreground", "#ffffff"),
                "surface": bg,
            },
            "dark_foreground_on_background": {
                "text": palette.get("dark_foreground", "#888888"),
                "surface": bg,
            },
            "light_foreground_on_background": {
                "text": palette.get("light_foreground", "#cccccc"),
                "surface": bg,
            },
            "bright_foreground_on_background": {
                "text": palette.get("bright_foreground", "#ffffff"),
                "surface": bg,
            },
            "accent_on_background": {
                "text": palette.get("accent", "#89b4fa"),
                "surface": bg,
            },
            "foreground_on_dark_background": {
                "text": palette.get("foreground", "#ffffff"),
                "surface": dark_bg,
            },
            "selection_foreground_on_selection": {
                "text": palette.get("selection_foreground", "#ffffff"),
                "surface": selection,
            },
        }

        results = {}
        all_aa = True
        for name, pair in checks.items():
            ratio = compute_contrast_ratio(pair["text"], pair["surface"])
            passes_aa = ratio >= 4.5
            passes_aa_large = ratio >= 3.0
            passes_aaa = ratio >= 7.0
            if not passes_aa:
                all_aa = False

            results[name] = {
                "ratio": ratio,
                "text_color": pair["text"],
                "surface_color": pair["surface"],
                "passes_wcag_aa": passes_aa,
                "passes_wcag_aa_large": passes_aa_large,
                "passes_wcag_aaa": passes_aaa,
            }

        return {
            "theme_name": theme_name,
            "mode": palette.get("mode", "dark"),
            "background_luminance": round(ColorRGB.from_hex(bg).relative_luminance(), 4),
            "overall_compliant_wcag_aa": all_aa,
            "checks": results,
        }


_THEMING_INSTANCE = OmarchyThemingEngineServiceImpl()


# Top-level tool entrypoints
def omarchy_list_themes(**kwargs: Any) -> list[dict[str, Any]]:
    return _THEMING_INSTANCE.list_themes(**kwargs)


def omarchy_get_theme_palette(theme_name: str, **kwargs: Any) -> dict[str, Any]:
    return _THEMING_INSTANCE.get_theme_palette(theme_name=theme_name, **kwargs)


def omarchy_render_theme_template(
    template_content: str,
    theme_name: str,
    **kwargs: Any,
) -> str:
    return _THEMING_INSTANCE.render_theme_template(
        template_content=template_content,
        theme_name=theme_name,
        **kwargs,
    )


def omarchy_validate_theme_contrast(theme_name: str, **kwargs: Any) -> dict[str, Any]:
    return _THEMING_INSTANCE.validate_theme_contrast(theme_name=theme_name, **kwargs)


class OmarchyThemingEnginePlugin(HarnessPlugin):
    """Harness Plugin for Omarchy Theming Engine, Palette Resolution, and Template Generation."""

    @property
    def name(self) -> str:
        return "plugin.omarchy_theming_engine"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return (
            "Omarchy Quattro theming engine, palette resolution, "
            "sed-compatible template renderer, and WCAG contrast analyzer."
        )

    @property
    def provides(self) -> list[ServiceKey[Any]]:
        return [OMARCHY_THEMING_ENGINE_SERVICE_KEY]

    @property
    def requires(self) -> list[ServiceKey[Any]]:
        return []

    async def on_load(self, context: ServiceContext) -> None:
        context.provide(OMARCHY_THEMING_ENGINE_SERVICE_KEY, _THEMING_INSTANCE)

    async def enable(self, context: ServiceContext) -> None:
        await self.on_load(context)

    async def on_disable(self) -> None:
        pass

    async def disable(self, context: Any = None) -> None:
        await self.on_disable()


plugin = OmarchyThemingEnginePlugin()
