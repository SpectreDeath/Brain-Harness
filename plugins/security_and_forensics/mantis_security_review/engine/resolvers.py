"""Single-seam IoC resolver factory for MantisSecurityReviewService (Rule 58)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from plugins.security_and_forensics.mantis_security_review.engine.models import (
    MANTIS_SECURITY_REVIEW_KEY,
    MantisSecurityReviewService,
)

if TYPE_CHECKING:
    from plugins.security_and_forensics.mantis_security_review.engine.core import MantisReviewEngine


def resolve_mantis_security_review(target: Any = None) -> MantisSecurityReviewService:
    """Resolve or construct MantisSecurityReviewService via single seam (Rule 58)."""
    from harness.kernel.context import ServiceContext
    from plugins.security_and_forensics.mantis_security_review.engine.core import MantisReviewEngine

    if target is not None:
        if isinstance(target, MantisSecurityReviewService):
            return target
        if isinstance(target, ServiceContext):
            if target.has(MANTIS_SECURITY_REVIEW_KEY):
                return target.require(MANTIS_SECURITY_REVIEW_KEY)
            engine = MantisReviewEngine()
            target.provide(MANTIS_SECURITY_REVIEW_KEY, engine)
            return engine
        if hasattr(target, "mantis_service") and isinstance(
            target.mantis_service, MantisSecurityReviewService
        ):
            return target.mantis_service

    return MantisReviewEngine()
