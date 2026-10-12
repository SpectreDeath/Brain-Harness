"""Single-seam resolver for WebwrightHarnessEngine per Rule 58."""

from __future__ import annotations

from pathlib import Path

from harness.kernel.context import ServiceContext
from harness.services.webwright_harness import WEBWRIGHT_HARNESS_KEY
from plugins.integration_and_io.webwright_harness.engine.service import WebwrightHarnessEngine


def resolve_webwright_engine(
    context: ServiceContext | None = None,
    base_dir: str | Path | None = None,
) -> WebwrightHarnessEngine:
    """Resolve Webwright engine from IoC container if plugin wraps engine, or instantiate fresh instance."""
    if context is not None:
        service = context.optional(WEBWRIGHT_HARNESS_KEY)
        if service is not None and hasattr(service, "_engine") and isinstance(service._engine, WebwrightHarnessEngine):
            return service._engine
    return WebwrightHarnessEngine(base_dir=base_dir)
