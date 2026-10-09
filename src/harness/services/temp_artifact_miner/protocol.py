"""Service Protocol and Typed IoC ServiceKey (Rule 2, Rule 49)."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from harness.kernel.context import ServiceKey
from harness.services.temp_artifact_miner.models import (
    BriefCatalog,
    CognitiveBifurcationReport,
    SandboxReport,
    VisualSalvageReport,
)


@runtime_checkable
class TempArtifactMinerService(Protocol):
    """Protocol for scanning and mining ephemeral artifacts, test sandboxes, and visual briefs."""

    def scan_briefs(
        self,
        temp_dir: Path | str | None = None,
        max_depth: int = 2,
        heavy_threshold: int = 100000,
    ) -> BriefCatalog:
        """Scan temporary stores for HTML visual briefs with heavy topology bounding."""
        ...

    def triage_sandbox(
        self,
        pytest_dir: Path | str | None = None,
        max_depth: int = 3,
    ) -> SandboxReport:
        """Triage ephemeral pytest sandbox directories with noise pruning."""
        ...

    def tail_diagnostic_log(
        self,
        log_path: Path | str,
        max_lines: int = 50,
    ) -> tuple[str, ...]:
        """Read trailing diagnostic log lines into a bounded ring buffer."""
        ...

    def generate_salvage_markdown(
        self,
        catalog: BriefCatalog,
        sandbox: SandboxReport | None = None,
    ) -> str:
        """Synthesize a high-density Markdown salvage index."""
        ...

    def bifurcate_brief(
        self,
        brief_path: Path | str,
        target_vault_dir: Path | str | None = None,
        target_docs_dir: Path | str | None = None,
    ) -> CognitiveBifurcationReport:
        """Dual-lens bifurcation: epistemic Knowledge Vault item + documentation salvage."""
        ...

    def salvage_diagrams(
        self,
        brief_path: Path | str,
        target_docs_dir: Path | str | None = None,
    ) -> VisualSalvageReport:
        """Extract Mermaid DAGs and visual briefs into repository documentation."""
        ...


TEMP_ARTIFACT_MINER_KEY = ServiceKey[TempArtifactMinerService]("temp_artifact_miner_service")
