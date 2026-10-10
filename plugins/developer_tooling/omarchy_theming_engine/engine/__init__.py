"""Omarchy Theming Engine subpackage facade with 100% backward compatibility."""

from .accessibility import audit_theme_contrast
from .color import ColorRGB, compute_contrast_ratio, mix_colors
from .core import OmarchyThemingEngineServiceImpl
from .models import (
    DEFAULT_OMARCHY_PATH,
    OMARCHY_THEMING_ENGINE_SERVICE_KEY,
    OmarchyThemingEngineService,
)
from .palette import parse_colors_file, resolve_palette
from .renderer import render_template
from .resolvers import resolve_omarchy_theming_engine
from .tools import (
    _THEMING_INSTANCE,
    omarchy_get_theme_palette,
    omarchy_list_themes,
    omarchy_render_theme_template,
    omarchy_validate_theme_contrast,
)

__all__ = [
    "DEFAULT_OMARCHY_PATH",
    "OMARCHY_THEMING_ENGINE_SERVICE_KEY",
    "ColorRGB",
    "OmarchyThemingEngineService",
    "OmarchyThemingEngineServiceImpl",
    "_THEMING_INSTANCE",
    "audit_theme_contrast",
    "compute_contrast_ratio",
    "mix_colors",
    "omarchy_get_theme_palette",
    "omarchy_list_themes",
    "omarchy_render_theme_template",
    "omarchy_validate_theme_contrast",
    "parse_colors_file",
    "render_template",
    "resolve_omarchy_theming_engine",
    "resolve_palette",
]
