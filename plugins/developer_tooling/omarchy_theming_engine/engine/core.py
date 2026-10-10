"""Core Omarchy Theming Engine service implementation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import structlog

from .accessibility import audit_theme_contrast
from .models import DEFAULT_OMARCHY_PATH
from .palette import parse_colors_file, resolve_palette
from .renderer import render_template

logger = structlog.get_logger(__name__)


class OmarchyThemingEngineServiceImpl:
    """Implementation of Omarchy Theming Engine service."""

    def __init__(self, source_dir: Path | str | None = None) -> None:
        self._source_dir_override = Path(source_dir) if source_dir else None
        self._palette_cache: dict[str, dict[str, str]] = {}

    @property
    def source_dir(self) -> Path:
        """Resolve base Omarchy repository directory."""
        if self._source_dir_override:
            return self._source_dir_override
        env_path = os.environ.get("OMARCHY_PATH")
        if env_path:
            return Path(env_path)
        return DEFAULT_OMARCHY_PATH

    @property
    def themes_dir(self) -> Path:
        """Directory path containing all Omarchy themes."""
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
            colors_file = theme_path / "theme.toml"

        raw_colors: dict[str, str] = {}
        if colors_file.exists():
            raw_colors = parse_colors_file(colors_file)

        resolved = resolve_palette(raw_colors, theme_path)
        self._palette_cache[clean_theme] = resolved
        return dict(resolved)

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

        return render_template(template_content, palette)

    def validate_theme_contrast(self, theme_name: str, **kwargs: Any) -> dict[str, Any]:
        """Analyze WCAG 2.1 contrast ratios and accessibility metrics for a theme."""
        palette = self.get_theme_palette(theme_name)
        return audit_theme_contrast(palette, theme_name)
