"""Standard Coordinator Service Implementation (Rule 49)."""

from __future__ import annotations

import os
from pathlib import Path

from harness.services.temp_artifact_miner.bifurcation import (
    bifurcate_brief as _bifurcate_brief,
)
from harness.services.temp_artifact_miner.models import (
    BriefCatalog,
    BriefCatalogItem,
    CognitiveBifurcationReport,
    SandboxReport,
    VisualSalvageReport,
)
from harness.services.temp_artifact_miner.parser import (
    parse_html_brief as _parse_html_brief,
)
from harness.services.temp_artifact_miner.salvage import (
    generate_salvage_markdown as _generate_salvage_markdown,
    salvage_diagrams as _salvage_diagrams,
)
from harness.services.temp_artifact_miner.sandbox import (
    tail_diagnostic_log as _tail_diagnostic_log,
    triage_sandbox as _triage_sandbox,
)
from harness.services.temp_artifact_miner.scanner import (
    scan_briefs as _scan_briefs,
)


class StandardTempArtifactMinerService:
    """Standard production implementation of TempArtifactMinerService."""

    def __init__(self, default_temp_dir: Path | None = None) -> None:
        if default_temp_dir is not None:
            self._default_temp_dir = Path(default_temp_dir)
        else:
            env_temp = os.environ.get("TEMP") or os.environ.get("TMP") or "/tmp"
            self._default_temp_dir = Path(env_temp)

    def parse_html_brief(
        self,
        file_path: Path,
        heavy_threshold: int = 100000,
    ) -> BriefCatalogItem:
        """Extract structured decision logic and Mermaid DAGs from an HTML visual brief (Rule 48)."""
        return _parse_html_brief(file_path=file_path, heavy_threshold=heavy_threshold)

    def scan_briefs(
        self,
        temp_dir: Path | str | None = None,
        max_depth: int = 2,
        heavy_threshold: int = 100000,
    ) -> BriefCatalog:
        """Scan the temporary directory for HTML visual briefs with bounded traversal (Rule 52)."""
        return _scan_briefs(
            temp_dir=temp_dir,
            max_depth=max_depth,
            heavy_threshold=heavy_threshold,
            default_temp_dir=self._default_temp_dir,
        )

    def triage_sandbox(
        self,
        pytest_dir: Path | str | None = None,
        max_depth: int = 3,
    ) -> SandboxReport:
        """Triage ephemeral pytest sandbox directories with noise pruning (Rule 52)."""
        return _triage_sandbox(
            pytest_dir=pytest_dir,
            max_depth=max_depth,
            default_temp_dir=self._default_temp_dir,
        )

    def tail_diagnostic_log(
        self,
        log_path: Path | str,
        max_lines: int = 50,
    ) -> tuple[str, ...]:
        """Read the trailing lines of an ephemeral diagnostic log into a bounded ring buffer (Rule 53)."""
        return _tail_diagnostic_log(log_path=log_path, max_lines=max_lines)

    def generate_salvage_markdown(
        self,
        catalog: BriefCatalog,
        sandbox: SandboxReport | None = None,
    ) -> str:
        """Generate a high-density Markdown summary of salvaged visual briefs and sandbox runs."""
        return _generate_salvage_markdown(catalog=catalog, sandbox=sandbox)

    def bifurcate_brief(
        self,
        brief_path: Path | str,
        target_vault_dir: Path | str | None = None,
        target_docs_dir: Path | str | None = None,
    ) -> CognitiveBifurcationReport:
        """Execute Dual-Lens Cognitive Bifurcation (Rule 40, Rule 41)."""
        return _bifurcate_brief(
            brief_path=brief_path,
            target_vault_dir=target_vault_dir,
            target_docs_dir=target_docs_dir,
        )

    def salvage_diagrams(
        self,
        brief_path: Path | str,
        target_docs_dir: Path | str | None = None,
    ) -> VisualSalvageReport:
        """Extract Mermaid DAGs and visual briefs into repository documentation."""
        return _salvage_diagrams(
            brief_path=brief_path,
            target_docs_dir=target_docs_dir,
        )
