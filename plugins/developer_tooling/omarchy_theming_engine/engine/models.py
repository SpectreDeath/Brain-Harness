"""Protocol and service keys for Omarchy Theming Engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey

DEFAULT_OMARCHY_PATH = Path(r"D:\GitHub\cloned\omarchy-quattro\omarchy-quattro")


@runtime_checkable
class OmarchyThemingEngineService(Protocol):
    """Protocol for Omarchy Theme management, palette extraction, and template rendering."""

    def list_themes(self, **kwargs: Any) -> list[dict[str, Any]]:
        """List all available Omarchy themes with color highlights."""
        ...

    def get_theme_palette(self, theme_name: str, **kwargs: Any) -> dict[str, Any]:
        """Load and resolve full semantic and ANSI color palette for a theme."""
        ...

    def render_theme_template(
        self,
        template_content: str,
        theme_name: str,
        **kwargs: Any,
    ) -> str:
        """Render template with {{ key }}, {{ key_strip }}, {{ key_rgb }}, and {{ mix ... }}."""
        ...

    def validate_theme_contrast(self, theme_name: str, **kwargs: Any) -> dict[str, Any]:
        """Analyze WCAG 2.1 contrast ratios and accessibility metrics for a theme."""
        ...


OMARCHY_THEMING_ENGINE_SERVICE_KEY = ServiceKey[OmarchyThemingEngineService](
    "service.omarchy_theming_engine"
)
