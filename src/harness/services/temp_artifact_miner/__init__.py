"""Temp Artifact Miner Service Subpackage Facade (Rule 49)."""

from __future__ import annotations

from harness.services.temp_artifact_miner.models import (
    BriefCatalog,
    BriefCatalogItem,
    CognitiveBifurcationReport,
    IsnadAttributionRecord,
    SandboxFixture,
    SandboxReport,
    VisualSalvageReport,
    compute_file_sha256,
    detect_brief_category,
)
from harness.services.temp_artifact_miner.protocol import (
    TEMP_ARTIFACT_MINER_KEY,
    TempArtifactMinerService,
)
from harness.services.temp_artifact_miner.resolvers import (
    resolve_temp_artifact_miner,
)
from harness.services.temp_artifact_miner.service import (
    StandardTempArtifactMinerService,
)

__all__ = [
    "BriefCatalog",
    "BriefCatalogItem",
    "CognitiveBifurcationReport",
    "IsnadAttributionRecord",
    "SandboxFixture",
    "SandboxReport",
    "StandardTempArtifactMinerService",
    "TEMP_ARTIFACT_MINER_KEY",
    "TempArtifactMinerService",
    "VisualSalvageReport",
    "compute_file_sha256",
    "detect_brief_category",
    "resolve_temp_artifact_miner",
]
