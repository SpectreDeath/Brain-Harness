"""Brain Artifact Miner Service — decomposed subpackage.

Extracts, indexes, and mines workspace artifacts, reusable scratch tools,
dual-transcript reasoning streams, and background task execution logs
from IDE brain workspace stores.
"""

from __future__ import annotations

import sys

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.services.brain_artifact_miner.export import (
    export_knowledge_item,
    generate_html_brief,
)
from harness.services.brain_artifact_miner.models import (
    ArtifactLifecycleEntry,
    ByteOffsetEntry,
    DualTranscriptStep,
    ScratchCatalog,
    ScratchCatalogItem,
    TaskTriageReport,
)
from harness.services.brain_artifact_miner.protocols import (
    BRAIN_ARTIFACT_MINER_KEY,
    BrainArtifactMinerService,
)
from harness.services.brain_artifact_miner.resolvers import (
    resolve_brain_artifact_miner,
)
from harness.services.brain_artifact_miner.scratch import (
    classify_script_ast,
    scan_scratch_tools,
)
from harness.services.brain_artifact_miner.service import (
    StandardBrainArtifactMinerService,
)
from harness.services.brain_artifact_miner.transcript import (
    build_offset_index,
    get_step,
    stream_steps,
)
from harness.services.brain_artifact_miner.triage import (
    triage_task_logs,
)

__all__ = [
    "ArtifactLifecycleEntry",
    "BRAIN_ARTIFACT_MINER_KEY",
    "BrainArtifactMinerService",
    "ByteOffsetEntry",
    "DualTranscriptStep",
    "ScratchCatalog",
    "ScratchCatalogItem",
    "StandardBrainArtifactMinerService",
    "TaskTriageReport",
    "build_offset_index",
    "classify_script_ast",
    "export_knowledge_item",
    "generate_html_brief",
    "get_step",
    "resolve_brain_artifact_miner",
    "scan_scratch_tools",
    "stream_steps",
    "triage_task_logs",
]
