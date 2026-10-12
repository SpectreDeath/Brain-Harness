"""Click group consolidation for self_eval per Rule 6."""

from __future__ import annotations

import click

from harness.commands.self_eval.agreement import drift_cmd, kappa_cmd
from harness.commands.self_eval.brief import brief_cmd
from harness.commands.self_eval.judge import judge_cmd
from harness.commands.self_eval.layer1 import layer1_cmd
from harness.commands.self_eval.regression import gate_cmd, regression_cmd


@click.group("eval")
def eval_group() -> None:
    """Self-Evaluating AI Pipeline — 3-layer LLM quality evaluation & statistical gating."""


# Consolidate command registrations in a single place per Rule 6
eval_group.add_command(layer1_cmd)
eval_group.add_command(judge_cmd)
eval_group.add_command(kappa_cmd)
eval_group.add_command(drift_cmd)
eval_group.add_command(regression_cmd)
eval_group.add_command(gate_cmd)
eval_group.add_command(brief_cmd)
