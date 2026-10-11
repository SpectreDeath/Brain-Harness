"""Single-seam IoC resolution and factory for BrainArtifactMinerService (Rule 58)."""

from __future__ import annotations

import sys

from harness.kernel.context import ServiceContext
from harness.services.brain_artifact_miner.protocols import (
    BRAIN_ARTIFACT_MINER_KEY,
    BrainArtifactMinerService,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def resolve_brain_artifact_miner(ctx: ServiceContext | None = None) -> BrainArtifactMinerService:
    """Resolve BrainArtifactMinerService from IoC context or fall back to standard implementation (Rule 58)."""
    if ctx is not None:
        svc = ctx.optional(BRAIN_ARTIFACT_MINER_KEY)
        if svc is not None and isinstance(svc, BrainArtifactMinerService):
            return svc
    from harness.services.brain_artifact_miner.service import StandardBrainArtifactMinerService

    return StandardBrainArtifactMinerService()


__all__ = ["resolve_brain_artifact_miner"]
