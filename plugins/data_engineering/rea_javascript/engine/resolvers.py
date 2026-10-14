"""Single-seam resolver factory for REA JavaScript engine (Rule 58)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from harness.kernel.context import ServiceContext
from harness.services.rea_javascript import REA_JAVASCRIPT_KEY

if TYPE_CHECKING:
    from . import ReaJavaScriptEngine


def resolve_rea_javascript_engine(
    ctx: Optional[ServiceContext] = None,
) -> ReaJavaScriptEngine:
    """Resolve ReaJavaScriptEngine from IoC ServiceContext with deterministic fallback (Rule 58)."""
    if ctx is not None:
        try:
            svc = ctx.optional(REA_JAVASCRIPT_KEY)
            if svc is not None and hasattr(svc, "_engine"):
                return svc._engine
        except Exception:
            pass
    from . import ReaJavaScriptEngine

    return ReaJavaScriptEngine()
