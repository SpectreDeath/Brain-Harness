"""Brain Artifact Miner service protocols and typed IoC keys (Rule 2, Rule 49)."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from harness.kernel.context import ServiceKey
from harness.services.brain_artifact_miner.models import ScratchCatalog, TaskTriageReport

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


@runtime_checkable
class BrainArtifactMinerService(Protocol):
    """Protocol for mining workspace artifacts, scratch tools, and transcripts."""

    def build_offset_index(self, path: Path) -> dict[int, tuple[int, int]]:
        """Build an O(1) binary byte-offset index table for a JSONL transcript (Rule 48)."""
        ...

    def get_step(
        self,
        transcript_path: Path,
        step_index: int,
        dereference_truncated: bool = True,
    ) -> dict[str, Any] | None:
        """Fetch a specific step via O(1) seek, dereferencing truncated steps (Rule 22, 48)."""
        ...

    def stream_steps(
        self,
        transcript_path: Path,
        dereference_truncated: bool = True,
    ) -> Iterator[dict[str, Any]]:
        """Stream all transcript steps with optional truncation dereferencing."""
        ...

    def scan_scratch_tools(self, brain_dir: Path, max_depth: int = 3) -> ScratchCatalog:
        """Scan and catalog reusable Python scratch tools via AST inspection (Rule 32, 52)."""
        ...

    def triage_task_logs(self, brain_dir: Path, max_depth: int = 4) -> TaskTriageReport:
        """Triage background subprocess task logs across the brain store (Rule 53)."""
        ...

    def generate_html_brief(self, data: dict[str, Any]) -> str:
        """Synthesize an HTML visual brief with double-brace escaped CSS/regex (Rule 51)."""
        ...

    def export_knowledge_item(
        self,
        output_dir: Path,
        ki_id: str,
        title: str,
        category: str,
        summary: str,
        claims: list[dict[str, Any]],
    ) -> tuple[Path, Path]:
        """Export canonical dual-file Knowledge Vault item with isnad claims (Rule 40, 41)."""
        ...


BRAIN_ARTIFACT_MINER_KEY: ServiceKey[BrainArtifactMinerService] = ServiceKey("service.brain_artifact_miner")

__all__ = [
    "BRAIN_ARTIFACT_MINER_KEY",
    "BrainArtifactMinerService",
]
