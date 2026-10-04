#!/usr/bin/env python3
"""Brain Artifact Miner Engine — Thin CLI Wrapper & Adapter (Rule 49).

Delegates domain logic to the micro-kernel service implementation in
harness.services.brain_artifact_miner while providing backward-compatible CLI
and module interface seams.

Enforces:
- Rule 12: Slotted & frozen dataclasses
- Rule 23, Rule 50: Windows UTF-8 codec and sys.path entrypoint invariant
- Rule 32: Defensive batch exception logging (never bare except: continue)
- Rule 33: JSON null-field fallback (dict.get("key") or [])
- Rule 48: Large corpus binary byte-offset seek invariant
- Rule 49: Skill-to-IoC micro-kernel seam elevation
- Rule 51: F-string doubled braces for HTML/CSS visual briefs
- Rule 52: Bounded directory traversal
- Rule 53: Subprocess stderr drainage and task triage
- Rule 57: Unique domain-prefixed module naming (brain_artifact_miner.py)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

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

from harness.services.brain_artifact_miner import (
    BRAIN_ARTIFACT_MINER_KEY,
    ArtifactLifecycleEntry,
    BrainArtifactMinerService,
    ByteOffsetEntry,
    DualTranscriptStep,
    ScratchCatalog,
    ScratchCatalogItem,
    StandardBrainArtifactMinerService,
    TaskTriageReport,
)

logger = logging.getLogger("brain_artifact_miner")

# Default service engine instance for standalone execution
_default_service = StandardBrainArtifactMinerService()


def build_offset_index(path: Path) -> dict[int, tuple[int, int]]:
    """Build an O(1) binary byte-offset index table for a JSONL transcript (Rule 48)."""
    return _default_service.build_offset_index(path)


def get_step(
    transcript_path: Path,
    step_index: int,
    dereference_truncated: bool = True,
) -> dict[str, Any] | None:
    """Fetch a specific step via O(1) seek, dereferencing truncated steps (Rule 22, 48)."""
    return _default_service.get_step(
        transcript_path=transcript_path,
        step_index=step_index,
        dereference_truncated=dereference_truncated,
    )


def stream_steps(
    transcript_path: Path,
    dereference_truncated: bool = True,
) -> Iterator[dict[str, Any]]:
    """Stream all transcript steps with optional truncation dereferencing."""
    return _default_service.stream_steps(
        transcript_path=transcript_path,
        dereference_truncated=dereference_truncated,
    )


def scan_scratch_tools(brain_dir: Path, max_depth: int = 3) -> ScratchCatalog:
    """Scan and catalog reusable Python scratch tools across conversation workspaces (Rule 32, 52)."""
    return _default_service.scan_scratch_tools(brain_dir=brain_dir, max_depth=max_depth)


def triage_task_logs(brain_dir: Path, max_depth: int = 4) -> TaskTriageReport:
    """Triage background subprocess task logs across the brain store (Rule 53)."""
    return _default_service.triage_task_logs(brain_dir=brain_dir, max_depth=max_depth)


def generate_html_brief(data: dict[str, Any]) -> str:
    """Synthesize an HTML visual brief with double-brace escaped CSS/regex (Rule 51)."""
    return _default_service.generate_html_brief(data=data)


def export_knowledge_item(
    output_dir: Path,
    ki_id: str,
    title: str,
    category: str,
    summary: str,
    claims: list[dict[str, Any]],
) -> tuple[Path, Path]:
    """Export canonical dual-file Knowledge Vault item with isnad claims (Rule 40, 41)."""
    return _default_service.export_knowledge_item(
        output_dir=output_dir,
        ki_id=ki_id,
        title=title,
        category=category,
        summary=summary,
        claims=claims,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Brain Artifact Miner Engine")
    subparsers = parser.add_subparsers(dest="command")

    # index command
    index_parser = subparsers.add_parser("index", help="Build O(1) byte offset index for transcript")
    index_parser.add_argument("path", type=Path, help="Path to transcript.jsonl")

    # step command
    step_parser = subparsers.add_parser("step", help="Fetch a step via O(1) seek")
    step_parser.add_argument("path", type=Path, help="Path to transcript.jsonl")
    step_parser.add_argument("step_index", type=int, help="Step index to retrieve")
    step_parser.add_argument("--no-dereference", action="store_true", help="Disable auto-dereference")

    # scan command
    scan_parser = subparsers.add_parser("scan", help="Scan and classify scratch tools")
    scan_parser.add_argument("--brain-dir", type=Path, default=Path(r"C:\Users\spectre\.gemini\antigravity-ide\brain"))
    scan_parser.add_argument("--depth", type=int, default=3)

    # triage command
    triage_parser = subparsers.add_parser("triage", help="Triage background task logs")
    triage_parser.add_argument("--brain-dir", type=Path, default=Path(r"C:\Users\spectre\.gemini\antigravity-ide\brain"))

    # brief command
    brief_parser = subparsers.add_parser("brief", help="Generate HTML visual brief")
    brief_parser.add_argument("--brain-dir", type=Path, default=Path(r"C:\Users\spectre\.gemini\antigravity-ide\brain"))

    args = parser.parse_args()

    if args.command == "index":
        idx = build_offset_index(args.path)
        print(f"Indexed {len(idx)} steps from {args.path}")
    elif args.command == "step":
        step = get_step(args.path, args.step_index, dereference_truncated=not args.no_dereference)
        if step:
            print(f"Retrieved Step {args.step_index} (dereferenced={step.get('dereferenced')}): {step.get('type')}")
        else:
            print(f"Step {args.step_index} not found.")
    elif args.command == "scan":
        catalog = scan_scratch_tools(args.brain_dir, max_depth=args.depth)
        print(f"Scanned {catalog.total_scanned} scratch scripts; classified {catalog.classified_count}.")
        for cat, items in catalog.items_by_category.items():
            print(f"  {cat}: {len(items)}")
    elif args.command == "triage":
        report = triage_task_logs(args.brain_dir)
        print(f"Triaged {report.total_tasks} tasks: {report.failed_count} failures, {report.deadlock_count} deadlocks.")
    elif args.command == "brief":
        catalog = scan_scratch_tools(args.brain_dir, max_depth=3)
        triage = triage_task_logs(args.brain_dir)
        html = generate_html_brief({
            "title": "Brain Artifact Miner Visual Brief",
            "total_dirs": len(list(args.brain_dir.iterdir())) if args.brain_dir.exists() else 0,
            "scratch_count": catalog.total_scanned,
            "task_count": triage.total_tasks,
            "failed_tasks": triage.failed_count,
            "categories": catalog.items_by_category,
        })
        out_path = Path(os.environ.get("TEMP", "/tmp")) / "brain_miner_brief.html"
        out_path.write_text(html, encoding="utf-8")
        print(f"Visual Brief written to: {out_path}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
