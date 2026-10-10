"""Standalone tool dispatch entrypoints matching plugin.json."""

from __future__ import annotations

from typing import Any

from .core import OmarchyThemingEngineServiceImpl

_THEMING_INSTANCE = OmarchyThemingEngineServiceImpl()


def omarchy_list_themes(**kwargs: Any) -> list[dict[str, Any]]:
    """List all bundled Omarchy desktop themes with metadata and color palette preview."""
    return _THEMING_INSTANCE.list_themes(**kwargs)


def omarchy_get_theme_palette(theme_name: str, **kwargs: Any) -> dict[str, Any]:
    """Retrieve fully resolved color palette for a theme, including ANSI and semantic aliases."""
    return _THEMING_INSTANCE.get_theme_palette(theme_name=theme_name, **kwargs)


def omarchy_render_theme_template(
    template_content: str,
    theme_name: str,
    **kwargs: Any,
) -> str:
    """Render a configuration template string using Omarchy theme tokens and mix functions."""
    return _THEMING_INSTANCE.render_theme_template(
        template_content=template_content,
        theme_name=theme_name,
        **kwargs,
    )


def omarchy_validate_theme_contrast(theme_name: str, **kwargs: Any) -> dict[str, Any]:
    """Calculate WCAG 2.1 relative luminance and contrast ratios between text and background."""
    return _THEMING_INSTANCE.validate_theme_contrast(theme_name=theme_name, **kwargs)
