"""Single-Seam IoC Resolver and Fallback Factory (Rule 58)."""

from __future__ import annotations

from pathlib import Path

from harness.kernel.context import ServiceContext
from harness.services.temp_artifact_miner.protocol import (
    TEMP_ARTIFACT_MINER_KEY,
    TempArtifactMinerService,
)
from harness.services.temp_artifact_miner.service import (
    StandardTempArtifactMinerService,
)


def resolve_temp_artifact_miner(
    ctx: ServiceContext | None = None,
    default_temp_dir: Path | None = None,
) -> TempArtifactMinerService:
    """Resolve TempArtifactMinerService from IoC context or fall back to standard implementation (Rule 58)."""
    if ctx is not None:
        svc = ctx.optional(TEMP_ARTIFACT_MINER_KEY)
        if svc is not None and isinstance(svc, TempArtifactMinerService):
            return svc
    return StandardTempArtifactMinerService(default_temp_dir=default_temp_dir)
