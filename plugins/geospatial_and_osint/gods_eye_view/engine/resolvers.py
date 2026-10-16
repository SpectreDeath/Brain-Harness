"""Single-seam resolver factory for GodsEyeViewEngine per AGENTS.md Rule 58."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from harness.kernel.context import ServiceContext

from .core import GodsEyeViewEngine

_GLOBAL_ENGINE: GodsEyeViewEngine | None = None


_GLOBAL_BRIDGE: Any | None = None


def resolve_gods_eye_view_engine(
    context: ServiceContext | None = None,
    data_dir: str | None = None,
) -> GodsEyeViewEngine:
    """Resolve GodsEyeViewEngine from IoC context or fallback to singleton instance."""
    global _GLOBAL_ENGINE
    if context is not None:
        try:
            from harness.services.gods_eye_view import GODS_EYE_VIEW_SERVICE_KEY
            service = context.optional(GODS_EYE_VIEW_SERVICE_KEY)
            if service is not None and hasattr(service, "_engine") and isinstance(service._engine, GodsEyeViewEngine):
                return service._engine
        except Exception:
            pass

    if _GLOBAL_ENGINE is None:
        _GLOBAL_ENGINE = GodsEyeViewEngine(data_dir=data_dir)
    return _GLOBAL_ENGINE


def resolve_node_cli_bridge() -> Any:
    """Resolve singleton NodeCliBridge instance for subprocess execution."""
    global _GLOBAL_BRIDGE
    if _GLOBAL_BRIDGE is None:
        from ..cli_bridge import NodeCliBridge
        _GLOBAL_BRIDGE = NodeCliBridge()
    return _GLOBAL_BRIDGE


__all__ = [
    "resolve_gods_eye_view_engine",
    "resolve_node_cli_bridge",
]
