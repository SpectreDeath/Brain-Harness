"""Single-seam resolver for Omarchy Theming Engine per AGENTS.md Rule 58."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .models import OMARCHY_THEMING_ENGINE_SERVICE_KEY, OmarchyThemingEngineService

if TYPE_CHECKING:
    from harness.kernel.context import ServiceContext


def resolve_omarchy_theming_engine(
    target: Any = None,
    **kwargs: Any,
) -> OmarchyThemingEngineService:
    """Resolve or instantiate authoritative OmarchyThemingEngineService instance (Rule 58).

    Args:
        target: Optional ServiceContext, existing service instance, or None.
        **kwargs: Optional arguments passed to OmarchyThemingEngineServiceImpl if instantiated.

    Returns:
        Authoritative OmarchyThemingEngineService instance.
    """
    from .core import OmarchyThemingEngineServiceImpl

    if target is None:
        return OmarchyThemingEngineServiceImpl(**kwargs)

    if isinstance(target, OmarchyThemingEngineService):
        return target

    if hasattr(target, "optional") and hasattr(target, "provide"):
        existing = target.optional(OMARCHY_THEMING_ENGINE_SERVICE_KEY)
        if existing is not None and isinstance(existing, OmarchyThemingEngineService):
            return existing
        service = OmarchyThemingEngineServiceImpl(**kwargs)
        target.provide(OMARCHY_THEMING_ENGINE_SERVICE_KEY, service)
        return service

    return OmarchyThemingEngineServiceImpl(**kwargs)
