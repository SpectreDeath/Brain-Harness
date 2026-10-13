"""Uncertainty-Aware AI Pipeline CLI commands — modular subpackage facade."""

from __future__ import annotations

from .adapter import UncertaintyEngineAdapter
from .brief import brief_cmd
from .calibrate import calibrate_cmd
from .gate import gate_cmd
from .group import uncertainty_group
from .logprobs import logprobs_cmd
from .pipeline import pipeline_cmd
from .resolver import (
    _EngineAdapter,
    get_uncertainty_service,
    resolve_uncertainty_service,
)
from .retrieval import retrieval_cmd

__all__ = [
    "UncertaintyEngineAdapter",
    "_EngineAdapter",
    "brief_cmd",
    "calibrate_cmd",
    "gate_cmd",
    "get_uncertainty_service",
    "logprobs_cmd",
    "pipeline_cmd",
    "resolve_uncertainty_service",
    "retrieval_cmd",
    "uncertainty_group",
]
