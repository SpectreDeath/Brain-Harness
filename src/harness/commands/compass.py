"""Headless Click CLI commands for HarnessCompass automatic harness evolution.

Rule 6: Single-source co-located Click group declaration.
Rule 10: Headless CLI inspection and export seams.
Rule 23: Windows UTF-8 stream codec entrypoint invariant.
"""

from __future__ import annotations

import json as _json
from pathlib import Path
import sys
from typing import Any

import click

# Rule 23: Windows UTF-8 Stream Codec Entrypoint Invariant
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from harness.services.harness_compass import (
    EvolutionRoundData,
    FeedbackItemData,
    GateResultData,
    GroundedEvidenceData,
    HarnessCompassService,
    HarnessEditData,
    IntegrationManifestData,
)


def get_harness_compass_service() -> HarnessCompassService:
    """Retrieve or bootstrap the HarnessCompass service singleton."""
    try:
        from plugins.agent_orchestration.harness_compass.main import plugin
        return plugin
    except Exception:
        # Fallback: bootstrap engine adapter directly
        _ws_root = Path(__file__).resolve().parents[3]
        _skill_scripts = (
            _ws_root / ".agents" / "skills" / "harness-compass" / "scripts"
        )
        if str(_skill_scripts) not in sys.path:
            sys.path.insert(0, str(_skill_scripts))

        from harness_compass_engine import HarnessCompassEngine

        class _EngineAdapter(HarnessCompassService):
            def __init__(self) -> None:
                self._eng = HarnessCompassEngine()

            def validate_edit(self, edit: HarnessEditData) -> GateResultData:
                from plugins.agent_orchestration.harness_compass.main import (
                    HarnessCompassPlugin,
                )
                p = HarnessCompassPlugin()
                return p.validate_edit(edit)

            def ground_feedback(
                self, item: FeedbackItemData, trajectory_turns: Any
            ) -> GroundedEvidenceData:
                from plugins.agent_orchestration.harness_compass.main import (
                    HarnessCompassPlugin,
                )
                p = HarnessCompassPlugin()
                return p.ground_feedback(item, trajectory_turns)

            def execute_r3_merge(
                self,
                winner_name: str,
                winner_score: float,
                winner_edits: Any,
                loser_name: str,
                loser_score: float,
                loser_edits: Any,
            ) -> IntegrationManifestData:
                from plugins.agent_orchestration.harness_compass.main import (
                    HarnessCompassPlugin,
                )
                p = HarnessCompassPlugin()
                return p.execute_r3_merge(
                    winner_name,
                    winner_score,
                    winner_edits,
                    loser_name,
                    loser_score,
                    loser_edits,
                )

            def simulate_round(
                self,
                round_num: int,
                baseline_score: float,
                structural_edits: Any,
                guidance_edits: Any,
                structural_score: float,
                guidance_score: float,
            ) -> EvolutionRoundData:
                from plugins.agent_orchestration.harness_compass.main import (
                    HarnessCompassPlugin,
                )
                p = HarnessCompassPlugin()
                return p.simulate_round(
                    round_num,
                    baseline_score,
                    structural_edits,
                    guidance_edits,
                    structural_score,
                    guidance_score,
                )

            def generate_visual_brief(
                self, output_path: str | Path | None = None
            ) -> Path:
                return self._eng.generate_visual_brief(output_path=output_path)

        return _EngineAdapter()


@click.group("compass")
def compass_group() -> None:
    """HarnessCompass CLI — Automatic harness discovery, calibration & R3 integration."""
    pass


@compass_group.command("gate")
@click.argument("content", type=str)
@click.option("--id", "edit_id", default="chg-01", help="Edit identifier")
@click.option(
    "--surface",
    "-s",
    default="systemprompt",
    type=click.Choice(
        [
            "middleware",
            "tool_impl",
            "sub_agent",
            "systemprompt",
            "skills",
            "tool_desc",
            "memory",
        ],
        case_sensitive=False,
    ),
    help="Target component surface",
)
@click.option("--description", "-d", default="Candidate edit", help="Edit description")
@click.option("--file", "target_file", default="systemprompt.md", help="Destination file")
@click.option(
    "--advisory/--no-advisory",
    default=True,
    help="Whether edit contains behavioral advice",
)
@click.option(
    "--executable/--no-executable",
    default=False,
    help="Whether edit contains deterministic executable code",
)
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def gate_cmd(
    content: str,
    edit_id: str,
    surface: str,
    description: str,
    target_file: str,
    advisory: bool,
    executable: bool,
    json_output: bool,
) -> None:
    """Validate a candidate harness edit against Content and Placement invariants."""
    svc = get_harness_compass_service()
    edit = HarnessEditData(
        id=edit_id,
        surface=surface,
        description=description,
        target_file=target_file,
        content=content,
        is_advisory=advisory,
        is_code_executable=executable,
    )
    result = svc.validate_edit(edit)

    if json_output:
        click.echo(_json.dumps(result.model_dump(), indent=2))
        return

    click.echo(f"Generalization Gate Evaluation for '{edit.id}':")
    click.echo(f"  Status:       {'PASSED' if result.passed else 'FAILED'}")
    click.echo(f"  Surface:      {edit.surface}")
    click.echo(f"  Target File:  {edit.target_file}")
    if result.violations:
        click.echo("  Violations:")
        for v in result.violations:
            click.echo(f"    - [{v.rule}] {v.detail}")
    else:
        click.echo("  Violations:   None (All invariants satisfied)")


@compass_group.command("feedback")
@click.argument("friction", type=str)
@click.option("--desired", default="Increase capability", help="Desired change")
@click.option(
    "--kind",
    type=click.Choice(["improve_existing", "new_capability"]),
    default="improve_existing",
    help="Feedback kind",
)
@click.option("--component", default="tool_impl", help="Component surface")
@click.option(
    "--trace-refs",
    default="turn_1",
    help="Comma-separated cited turn IDs (e.g. turn_1,turn_4)",
)
@click.option(
    "--attribution",
    type=click.Choice(["harness", "agent_reasoning", "task_ambiguity", "environment"]),
    default="harness",
    help="Failure attribution source",
)
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def feedback_cmd(
    friction: str,
    desired: str,
    kind: str,
    component: str,
    trace_refs: str,
    attribution: str,
    json_output: bool,
) -> None:
    """Ground agent usability feedback against execution traces."""
    svc = get_harness_compass_service()
    refs = [r.strip() for r in trace_refs.split(",") if r.strip()]
    # Mock trajectory turns matching refs for demonstration
    mock_turns = [{"turn_id": r} for r in refs]

    item = FeedbackItemData(
        kind=kind,
        component=component,
        friction=friction,
        desired_change=desired,
        trace_refs=refs,
        attribution=attribution,
    )
    res = svc.ground_feedback(item, mock_turns)

    if json_output:
        click.echo(_json.dumps(res.model_dump(), indent=2))
        return

    click.echo(f"Feedback Grounding Verification:")
    click.echo(f"  Grounded:         {'YES' if res.grounded else 'NO'}")
    click.echo(f"  Assigned Track:   {res.assigned_track.upper()}")
    click.echo(f"  Confidence:       {res.confidence:.2f}")
    if res.rejection_reason:
        click.echo(f"  Rejection Reason: {res.rejection_reason}")


@compass_group.command("merge")
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def merge_cmd(json_output: bool) -> None:
    """Execute R3 integration: Revision, Recombination, and Occam's Razor Refinement."""
    svc = get_harness_compass_service()

    winner_edits = [
        HarnessEditData(
            id="win-code-01",
            surface="middleware",
            description="Isolated virtual environment test runner enforcing execution validation",
            target_file="middleware/test_runner.py",
            content="def run_isolated_test(): pass",
            is_code_executable=True,
        )
    ]

    loser_edits = [
        HarnessEditData(
            id="lose-adv-01",
            surface="systemprompt",
            description="Advisory rule for isolated virtual environment test execution",
            target_file="systemprompt.md",
            content="Remember to always run tests inside an isolated virtual environment to validate execution.",
            is_advisory=True,
        ),
        HarnessEditData(
            id="lose-valid-02",
            surface="systemprompt",
            description="Prioritize minimal reproduction scripts",
            target_file="systemprompt.md",
            content="Formulate narrowest reproduction script before code modification.",
            is_advisory=True,
        ),
        HarnessEditData(
            id="lose-bad-03",
            surface="systemprompt",
            description="Task specific token hack",
            target_file="systemprompt.md",
            content="Task sympy-1244 fix.",
            is_advisory=True,
        ),
    ]

    manifest = svc.execute_r3_merge(
        winner_name="Track A (Structural)",
        winner_score=0.66,
        winner_edits=winner_edits,
        loser_name="Track B (Guidance)",
        loser_score=0.62,
        loser_edits=loser_edits,
    )

    if json_output:
        click.echo(_json.dumps(manifest.model_dump(), indent=2))
        return

    click.echo("R3 Integration Manifest:")
    click.echo(f"  Winner Base:      {manifest.base_winner} ({manifest.winner_score:.1%})")
    click.echo(f"  Kept from Loser:  {len(manifest.kept_from_loser)} edits")
    for k in manifest.kept_from_loser:
        click.echo(f"    + [{k['change']}] {k['why']}")
    click.echo(f"  Dropped from Loser: {len(manifest.dropped_from_loser)} edits")
    for d in manifest.dropped_from_loser:
        click.echo(f"    - [{d['change']}] {d['why']}")
    click.echo(f"  Occam Redundancy:   {len(manifest.removed_as_redundant)} rules purged")
    for r in manifest.removed_as_redundant:
        click.echo(f"    * [{r['change']}] {r['why']}")


@compass_group.command("run")
@click.option("--round-num", "-r", default=1, help="Evolution round index")
@click.option("--baseline", "-b", default=0.54, help="Starting baseline Pass@1")
@click.option(
    "--structural-score",
    "-s",
    default=0.66,
    help="Track A (Structural) score",
)
@click.option(
    "--guidance-score",
    "-g",
    default=0.62,
    help="Track B (Guidance) score",
)
@click.option("--json-output", is_flag=True, help="Emit raw JSON output")
def run_cmd(
    round_num: int,
    baseline: float,
    structural_score: float,
    guidance_score: float,
    json_output: bool,
) -> None:
    """Simulate a complete 5-stage evolution round with acceptance gating."""
    svc = get_harness_compass_service()

    s_edits = [
        HarnessEditData(
            id="s-01",
            surface="middleware",
            description="Patch guard blocking invalid syntax",
            target_file="middleware/guard.py",
            content="def guard(): pass",
            is_code_executable=True,
        )
    ]
    g_edits = [
        HarnessEditData(
            id="g-01",
            surface="systemprompt",
            description="General reproduction guidance",
            target_file="systemprompt.md",
            content="Formulate narrowest reproduction script.",
            is_advisory=True,
        )
    ]

    res = svc.simulate_round(
        round_num=round_num,
        baseline_score=baseline,
        structural_edits=s_edits,
        guidance_edits=g_edits,
        structural_score=structural_score,
        guidance_score=guidance_score,
    )

    if json_output:
        click.echo(_json.dumps(res.model_dump(), indent=2))
        return

    click.echo(f"Evolution Round {res.round_num} Result:")
    click.echo(f"  Baseline Pass@1:   {res.baseline_score:.1%}")
    click.echo(f"  Structural Score:  {res.structural_score:.1%}")
    click.echo(f"  Guidance Score:    {res.guidance_score:.1%}")
    click.echo(f"  Winning Track:     {res.winner_track.upper()} ({res.winner_score:.1%})")
    click.echo(f"  Acceptance Status: {'ACCEPTED (Champion Updated)' if res.accepted else 'REJECTED (Rolled Back)'}")
    click.echo(f"  Notes:             {res.notes}")


@compass_group.command("brief")
@click.option("--output", "-o", default=None, help="Output file path for HTML brief")
def brief_cmd(output: str | None) -> None:
    """Generate interactive standalone HTML visual brief."""
    svc = get_harness_compass_service()
    brief_path = svc.generate_visual_brief(output)
    click.echo(f"HarnessCompass Visual Brief generated: {brief_path}")
