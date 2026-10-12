"""Two-Tier Context Staging ($T_4$) simulation Click command."""

from __future__ import annotations

import json as _json
from typing import Any

import click

from harness.commands.calibrator.resolver import get_calibrator_service


@click.command("staging")
@click.option(
    "--budget",
    "-b",
    "usable_window",
    type=int,
    default=100000,
    help="Usable context window budget",
)
@click.option(
    "--turns",
    "-t",
    type=int,
    default=10,
    help="Number of turns to simulate",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    help="Output simulation result as structured JSON",
)
def calibrator_staging_cli(
    usable_window: int,
    turns: int,
    as_json: bool,
) -> None:
    """Simulate Two-Tier Context Staging ($T_4$) over an execution transcript."""
    service = get_calibrator_service()

    # Generate synthetic transcript turns to demonstrate B1 elision & B2 summarization
    events: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": "You are a calibrated autonomous coding assistant.",
            "turn": 0,
            "token_count": 2500,
            "is_bulky": False,
        }
    ]

    for turn_idx in range(1, turns + 1):
        events.append(
            {
                "role": "user",
                "content": f"Execute step {turn_idx} of repository refactoring task.",
                "turn": turn_idx,
                "token_count": 1200,
                "is_bulky": False,
            }
        )
        events.append(
            {
                "role": "tool_call",
                "content": f"read_file(path='module_{turn_idx}.py')",
                "turn": turn_idx,
                "token_count": 400,
                "is_bulky": False,
            }
        )
        is_bulky = turn_idx in (2, 3, 4, 5)
        obs_tokens = 15000 if is_bulky else 1500
        events.append(
            {
                "role": "tool_observation",
                "content": f"Source dump for module_{turn_idx} with {obs_tokens * 4} chars of code and symbols.",
                "turn": turn_idx,
                "token_count": obs_tokens,
                "is_bulky": is_bulky,
                "tool_name": "read_file",
            }
        )

    sim = service.simulate_staging(events=events, usable_window=usable_window)

    if as_json:
        click.echo(_json.dumps(sim.model_dump(), indent=2))
        return

    click.echo(
        click.style(
            "=== Two-Tier Context Staging ($T_4$) Simulation ===", fg="cyan", bold=True
        )
    )
    click.echo(f"Usable Window: {sim.usable_window:,} tokens")
    click.echo(f"Initial Token Count: {sim.initial_tokens:,} tokens")
    click.echo(
        f"Soft Threshold B1 (0.60) Elision: "
        f"{'TRIGGERED' if sim.b1_elision_triggered else 'NOT TRIGGERED'}"
    )
    click.echo(
        f"Hard Threshold B2 (0.85) Summary: "
        f"{'TRIGGERED' if sim.b2_summary_triggered else 'NOT TRIGGERED'}"
    )
    click.echo(f"Elided Bulky Observations: {sim.elided_observations_count}")
    click.echo(f"Pruned Tokens: {sim.pruned_tokens_count:,}")
    click.echo(
        f"Final Staged Tokens: {click.style(f'{sim.final_tokens:,}', fg='green', bold=True)} tokens"
    )
    if sim.structured_summary:
        click.echo("\nGenerated 7-Heading Structured Summary:")
        for line in sim.structured_summary.splitlines():
            click.echo(f"  {line}")
