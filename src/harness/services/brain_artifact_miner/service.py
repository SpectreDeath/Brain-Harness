"""Authoritative standard implementation of BrainArtifactMinerService."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from harness.services.brain_artifact_miner.export import (
    export_knowledge_item,
    generate_html_brief,
)
from harness.services.brain_artifact_miner.models import (
    ScratchCatalog,
    TaskTriageReport,
)
from harness.services.brain_artifact_miner.scratch import (
    classify_script_ast,
    scan_scratch_tools,
)
from harness.services.brain_artifact_miner.transcript import (
    build_offset_index,
    get_step,
    stream_steps,
)
from harness.services.brain_artifact_miner.triage import triage_task_logs

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


class StandardBrainArtifactMinerService:
    """Authoritative standard implementation of BrainArtifactMinerService."""

    def __init__(self) -> None:
        self._offset_cache: dict[Path, dict[int, tuple[int, int]]] = {}

    def build_offset_index(self, path: Path) -> dict[int, tuple[int, int]]:
        """Build an O(1) binary byte-offset index table for a JSONL transcript (Rule 48)."""
        return build_offset_index(path, cache=self._offset_cache)

    def get_step(
        self,
        transcript_path: Path,
        step_index: int,
        dereference_truncated: bool = True,
    ) -> dict[str, Any] | None:
        """Fetch a specific step via O(1) seek, dereferencing truncated steps (Rule 22, 48)."""
        return get_step(
            transcript_path,
            step_index,
            dereference_truncated=dereference_truncated,
            cache=self._offset_cache,
        )

    def stream_steps(
        self,
        transcript_path: Path,
        dereference_truncated: bool = True,
    ) -> Iterator[dict[str, Any]]:
        """Stream all transcript steps with optional truncation dereferencing."""
        return stream_steps(
            transcript_path,
            dereference_truncated=dereference_truncated,
            cache=self._offset_cache,
        )

    def _classify_script_ast(
        self,
        code: str,
        file_path: Path,
    ) -> tuple[str, list[str], list[str], str]:
        """Inspect a Python script via AST to extract metadata and category (Rule 42)."""
        return classify_script_ast(code, file_path)

    def scan_scratch_tools(self, brain_dir: Path, max_depth: int = 3) -> ScratchCatalog:
        """Scan and catalog reusable Python scratch tools across conversation workspaces."""
        return scan_scratch_tools(brain_dir, max_depth=max_depth)

    def triage_task_logs(self, brain_dir: Path, max_depth: int = 4) -> TaskTriageReport:
        """Triage background subprocess task logs across the brain store (Rule 53)."""
        return triage_task_logs(brain_dir, max_depth=max_depth)

    def generate_html_brief(self, data: dict[str, Any]) -> str:
        """Synthesize an HTML visual brief with double-brace escaped CSS/regex (Rule 51)."""
        return generate_html_brief(data)

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
        return export_knowledge_item(
            output_dir, ki_id, title, category, summary, claims
        )


__all__ = ["StandardBrainArtifactMinerService"]
