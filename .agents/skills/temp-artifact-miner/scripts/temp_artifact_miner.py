#!/usr/bin/env python3
"""Temp Artifact Miner Engine — Thin CLI Wrapper & Adapter (Rule 49).

Delegates domain logic to the micro-kernel service implementation in
harness.services.temp_artifact_miner while providing backward-compatible CLI
and module interface seams.

Enforces:
- Rule 12: Slotted & frozen dataclasses
- Rule 23, Rule 50: Windows UTF-8 codec and sys.path entrypoint invariant
- Rule 32: Defensive batch exception logging (never bare except: continue)
- Rule 33: JSON null-field fallback (dict.get("key") or [])
- Rule 48: Large file handling & heavy topology bounding
- Rule 49: Skill-to-IoC micro-kernel seam elevation
- Rule 51: F-string doubled braces for HTML/CSS visual briefs
- Rule 52: Bounded directory traversal
- Rule 53: Subprocess stderr drainage and ring-buffer log triage
- Rule 57: Unique domain-prefixed module naming (temp_artifact_miner.py)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import asdict
from pathlib import Path

# Windows UTF-8 stream codec & sys.path precedence invariant (Rule 23, 50)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(WORKSPACE_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT / "src"))
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from harness.services.temp_artifact_miner import (
    TEMP_ARTIFACT_MINER_KEY,
    BriefCatalog,
    BriefCatalogItem,
    CognitiveBifurcationReport,
    SandboxFixture,
    SandboxReport,
    StandardTempArtifactMinerService,
    TempArtifactMinerService,
    VisualSalvageReport,
    detect_brief_category,
)

logger = logging.getLogger("temp_artifact_miner")

# Default service engine instance for standalone execution
_default_service = StandardTempArtifactMinerService()


def parse_html_brief(file_path: Path, heavy_threshold: int = 100000) -> BriefCatalogItem:
    """Extract structured decision logic and Mermaid DAGs from an HTML visual brief (Rule 48)."""
    return _default_service.parse_html_brief(file_path, heavy_threshold=heavy_threshold)


def scan_temp_briefs(temp_path: Path, max_depth: int = 2, heavy_threshold: int = 100000) -> BriefCatalog:
    """Scan the temporary directory for HTML visual briefs with bounded traversal (Rule 52)."""
    return _default_service.scan_briefs(temp_dir=temp_path, max_depth=max_depth, heavy_threshold=heavy_threshold)


def triage_pytest_sandboxes(temp_path: Path, max_depth: int = 3) -> SandboxReport:
    """Triage ephemeral pytest sandbox directories (Rule 52, 53)."""
    return _default_service.triage_sandbox(pytest_dir=temp_path, max_depth=max_depth)


def tail_diagnostic_log(log_path: Path, max_lines: int = 50) -> list[str]:
    """Read the trailing lines of an ephemeral diagnostic log into a bounded ring buffer (Rule 53)."""
    return list(_default_service.tail_diagnostic_log(log_path, max_lines=max_lines))


def generate_salvage_markdown(catalog: BriefCatalog) -> str:
    """Generate a high-density Markdown summary of salvaged visual briefs."""
    return _default_service.generate_salvage_markdown(catalog)


def bifurcate_brief(
    brief_path: Path | str,
    target_vault_dir: Path | str | None = None,
    target_docs_dir: Path | str | None = None,
) -> CognitiveBifurcationReport:
    """Execute Dual-Lens Cognitive Bifurcation (Rule 40, Rule 41)."""
    return _default_service.bifurcate_brief(
        brief_path=brief_path,
        target_vault_dir=target_vault_dir,
        target_docs_dir=target_docs_dir,
    )


def main() -> None:
    """CLI entrypoint for standalone execution."""
    parser = argparse.ArgumentParser(description="Temp Artifact Miner CLI")
    parser.add_argument(
        "--temp-dir",
        type=str,
        default=os.environ.get("TEMP") or os.environ.get("TMP") or r"C:\Users\spectre\AppData\Local\Temp",
        help="Path to temporary directory",
    )
    parser.add_argument("--scan", action="store_true", help="Scan HTML visual briefs")
    parser.add_argument("--sandbox", action="store_true", help="Triage pytest sandbox runs")
    parser.add_argument("--salvage-md", action="store_true", help="Emit markdown salvage report")
    parser.add_argument("--bifurcate", type=str, default=None, help="Bifurcate an HTML brief into vault and docs")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    temp_path = Path(args.temp_dir)

    if args.bifurcate:
        report = bifurcate_brief(args.bifurcate)
        if args.json:
            print(json.dumps(asdict(report), indent=2))
        else:
            print(f"Bifurcation Completed for {report.source_name}:")
            print(f"  Knowledge Vault: {report.knowledge_vault_path}")
            print(f"  Permanent Doc:   {report.salvaged_doc_path}")
        return

    if args.sandbox:
        report = triage_pytest_sandboxes(temp_path)
        if args.json:
            print(json.dumps(asdict(report), indent=2))
        else:
            print(f"Pytest Sandbox Runs: {report.total_runs}")
            for r in report.runs:
                print(f"  - {r.name}: {r.fixture_count} fixtures, {len(r.mock_skills)} mock skills")
        return

    catalog = scan_temp_briefs(temp_path)

    if args.salvage_md:
        md = generate_salvage_markdown(catalog)
        print(md)
        return

    if args.json:
        data = {
            "total_scanned": catalog.total_scanned,
            "brief_count": catalog.brief_count,
            "total_bytes": catalog.total_bytes,
            "heavy_count": catalog.heavy_count,
            "categories": {cat: [asdict(i) for i in items] for cat, items in catalog.items_by_category.items()},
        }
        print(json.dumps(data, indent=2))
    else:
        print(f"Scanned {catalog.brief_count} briefs ({catalog.total_bytes / (1024*1024):.2f} MB)")
        for cat, items in catalog.items_by_category.items():
            print(f"  [{cat}]: {len(items)} briefs")


if __name__ == "__main__":
    main()
