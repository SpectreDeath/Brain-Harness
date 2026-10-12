"""Self-Evaluating AI Pipeline CLI commands — modular subpackage facade."""

from __future__ import annotations

from harness.commands.self_eval.agreement import drift_cmd, kappa_cmd
from harness.commands.self_eval.brief import brief_cmd
from harness.commands.self_eval.engine_adapter import (
    SelfEvaluatingPipelineEngineAdapter,
)
from harness.commands.self_eval.group import eval_group
from harness.commands.self_eval.judge import judge_cmd
from harness.commands.self_eval.layer1 import layer1_cmd
from harness.commands.self_eval.regression import gate_cmd, regression_cmd
from harness.commands.self_eval.resolver import get_self_eval_service

__all__ = [
    "SelfEvaluatingPipelineEngineAdapter",
    "brief_cmd",
    "drift_cmd",
    "eval_group",
    "gate_cmd",
    "get_self_eval_service",
    "judge_cmd",
    "kappa_cmd",
    "layer1_cmd",
    "regression_cmd",
]
