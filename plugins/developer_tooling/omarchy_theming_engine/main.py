"""Omarchy Quattro Theming Engine & Template Renderer Plugin Entrypoint.

Provides TOML palette parsing, legacy alias resolution, sed-compatible template
interpolation, mix/gradient evaluations, and WCAG 2.1 accessibility auditing.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any

# Ensure Harness core src is on sys.path for isolated subprocesses
_HARNESS_SRC = Path(__file__).resolve().parents[3] / "src"
if _HARNESS_SRC.exists() and str(_HARNESS_SRC) not in sys.path:
    sys.path.insert(0, str(_HARNESS_SRC))

if __name__ not in sys.modules:
    sys.modules[__name__] = sys.modules.get("__main__") or types.ModuleType(__name__)

from harness.kernel.context import ServiceContext, ServiceKey
from harness.plugins.base import HarnessPlugin

from .engine import (
    DEFAULT_OMARCHY_PATH,
    OMARCHY_THEMING_ENGINE_SERVICE_KEY,
    ColorRGB,
    OmarchyThemingEngineService,
    OmarchyThemingEngineServiceImpl,
    _THEMING_INSTANCE,
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

__all__ = [
    "DEFAULT_OMARCHY_PATH",
    "OMARCHY_THEMING_ENGINE_SERVICE_KEY",
    "ColorRGB",
    "OmarchyThemingEnginePlugin",
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
    "plugin",
    "render_template",
    "resolve_omarchy_theming_engine",
    "resolve_palette",
]
