"""Visual HTML brief generation Click command."""

from __future__ import annotations

import json as _json
from pathlib import Path

import click

from harness.commands.self_eval.resolver import get_self_eval_service


@click.command("brief")
@click.option(
    "--result", "result_path", required=True, help="Path to regression JSON result"
)
@click.option(
    "--gate", "gate_path", default=None, help="Optional path to statistical gate JSON"
)
@click.option(
    "--output", "output_path", default=None, help="Destination HTML file path"
)
def brief_cmd(
    result_path: str,
    gate_path: str | None,
    output_path: str | None,
) -> None:
    """Generate standalone interactive HTML visual brief in %TEMP%."""
    svc = get_self_eval_service()
    reg_data = _json.loads(Path(result_path).read_text(encoding="utf-8"))
    gate_data = (
        _json.loads(Path(gate_path).read_text(encoding="utf-8")) if gate_path else None
    )

    out_file = svc.generate_visual_brief(
        regression_data=reg_data,
        gate_data=gate_data,
        output_path=output_path,
    )
    click.echo(f"Visual Brief generated: {out_file.resolve()}")
