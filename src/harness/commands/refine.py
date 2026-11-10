"""`harness refine` -- headless inspection of recursive-harnessing seams (Rule 10).

Subcommands: `budget` (the R=4k / P=3k identity), `validate` (editable-surface check with
retry-ready prose), `scan` (evidence-isolation tripwires), `fingerprint` (trial identity) and
`demo` (deterministic, credential-free end-to-end run). All output is JSON.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from harness.services.recursive_harnessing import (
    BRAIN_SURFACE,
    EvidenceLeakError,
    SurfaceSpec,
    assert_no_leak_paths,
    assert_no_verdicts,
    expected_rollouts,
    expected_sessions,
    fingerprint_dir,
)
from harness.services.recursive_harnessing import surface as surface_ops
from harness.services.recursive_harnessing.demo import run_demo

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8")


def _emit(payload: dict) -> None:
    click.echo(json.dumps(payload, indent=2, default=str))


@click.group("refine")
def refine_group() -> None:
    """Recursive harnessing (Propose-Probe-Compose) -- inspection and demo seams."""


@refine_group.command("budget")
@click.option("--k", type=click.IntRange(min=1), required=True, help="Recursion budget k.")
def budget_cmd(k: int) -> None:
    """Print the expected rollout/session budget: R = 4k rollouts, P = 3k stages."""
    _emit({"k": k, "rollouts": expected_rollouts(k), "sessions": expected_sessions(k)})


@refine_group.command("validate")
@click.argument("harness_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--brain", is_flag=True, help="Use the Brain Harness surface (AGENTS.md + .agents/skills).")
@click.option("--skill-dir", default="skills", show_default=True)
@click.option("--always-on", "always_on", multiple=True, default=("AGENTS.md",), show_default=True)
@click.option("--always-on-max", type=click.IntRange(min=1), default=24_000, show_default=True)
def validate_cmd(
    harness_dir: Path, brain: bool, skill_dir: str, always_on: tuple[str, ...], always_on_max: int
) -> None:
    """Validate a harness directory against the editable surface; exit 1 with every problem."""
    spec = (
        BRAIN_SURFACE
        if brain
        else SurfaceSpec(name="cli", always_on=tuple(always_on), always_on_max=always_on_max, skill_dir=skill_dir)
    )
    rejected: list[str] = []
    tree = surface_ops.read_tree(spec, harness_dir, rejected=rejected)
    try:
        census = surface_ops.validate(spec, tree)
    except ValueError as exc:
        _emit({"valid": False, "errors": str(exc).split(" | "), "off_surface": sorted(rejected)})
        raise SystemExit(1) from exc
    _emit({"valid": True, "census": census, "off_surface": sorted(rejected)})


@refine_group.command("scan")
@click.argument("evidence_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--leak-glob", "leak_globs", multiple=True, help="Answer-key glob (repeatable).")
@click.option("--max-depth", type=click.IntRange(min=1), default=8, show_default=True)
def scan_cmd(evidence_dir: Path, leak_globs: tuple[str, ...], max_depth: int) -> None:
    """Run the answer-key and grader-verdict tripwires over an evidence tree; exit 1 on a leak."""
    try:
        assert_no_leak_paths(evidence_dir, leak_globs, max_depth=max_depth)
        assert_no_verdicts(evidence_dir, max_depth=max_depth)
    except EvidenceLeakError as exc:
        _emit({"clean": False, "error": str(exc)})
        raise SystemExit(1) from exc
    _emit({"clean": True, "root": str(evidence_dir)})


@refine_group.command("fingerprint")
@click.argument("harness_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
def fingerprint_cmd(harness_dir: Path) -> None:
    """Print the stable trial-identity fingerprint of a harness directory."""
    _emit({"path": str(harness_dir), "fingerprint": fingerprint_dir(harness_dir)})


@refine_group.command("demo")
@click.option("--output", type=click.Path(path_type=Path), required=True, help="Working directory.")
@click.option("--k", type=click.IntRange(min=1, max=4), default=1, show_default=True)
@click.option("--mode", type=click.Choice(["agg", "seq", "both"]), default="both", show_default=True)
def demo_cmd(output: Path, k: int, mode: str) -> None:
    """Run both recursion modes on a deterministic task; no model credentials required."""
    _emit(run_demo(output, k=k, mode=mode))
