"""Single-seam resolver factory for HfDatasetsService per AGENTS.md Rule 58."""

from __future__ import annotations

from typing import Any

from .protocol import HF_DATASETS_SERVICE_KEY, HfDatasetsService
from .service import DefaultHfDatasetsService


def resolve_hf_datasets_service(context: Any = None) -> HfDatasetsService:
    """Resolve or construct an authoritative HfDatasetsService instance (Rule 58).

    If an IoC container is supplied with an active binding, resolves it directly.
    Otherwise, instantiates a DefaultHfDatasetsService and registers it into the container if possible.
    """
    if context is not None:
        if hasattr(context, "optional"):
            svc = context.optional(HF_DATASETS_SERVICE_KEY)
            if svc is not None and isinstance(svc, HfDatasetsService):
                return svc
        elif hasattr(context, "require"):
            try:
                svc = context.require(HF_DATASETS_SERVICE_KEY)
                if svc is not None and isinstance(svc, HfDatasetsService):
                    return svc
            except Exception:
                pass

    service = DefaultHfDatasetsService()
    if context is not None and hasattr(context, "provide"):
        try:
            context.provide(HF_DATASETS_SERVICE_KEY, service, provider="core")
        except Exception:
            pass
    return service
