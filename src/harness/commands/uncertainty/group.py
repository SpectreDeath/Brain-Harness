"""Click group consolidation for uncertainty commands per Rule 6."""

from __future__ import annotations

import sys
import click

from .brief import brief_cmd
from .calibrate import calibrate_cmd
from .gate import gate_cmd
from .logprobs import logprobs_cmd
from .pipeline import pipeline_cmd
from .retrieval import retrieval_cmd


@click.group("uncertainty")
def uncertainty_group() -> None:
    """Uncertainty-Aware AI Pipeline — 3-Layer Interception & Overconfidence Mitigation."""
    # Ensure Windows UTF-8 stream codec entrypoint invariant (Rule 23)
    if sys.platform == "win32":
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


# Consolidate command registrations in a single place per Rule 6
uncertainty_group.add_command(gate_cmd, name="gate")
uncertainty_group.add_command(retrieval_cmd, name="retrieval")
uncertainty_group.add_command(logprobs_cmd, name="logprobs")
uncertainty_group.add_command(pipeline_cmd, name="pipeline")
uncertainty_group.add_command(calibrate_cmd, name="calibrate")
uncertainty_group.add_command(brief_cmd, name="brief")
