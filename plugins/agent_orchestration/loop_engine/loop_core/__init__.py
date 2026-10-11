"""Goal-Directed Loop Engine: Task Graph DAG, Tri-State Polling, Stepwise Control, and Checkpointing."""

from __future__ import annotations

import sys

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from plugins.agent_orchestration.loop_engine.loop_core.checkpoint import (
    export_controller_checkpoint,
    restore_controller_checkpoint,
)
from plugins.agent_orchestration.loop_engine.loop_core.controller import LoopController
from plugins.agent_orchestration.loop_engine.loop_core.graph import TaskGraph
from plugins.agent_orchestration.loop_engine.loop_core.models import (
    IterationSnapshot,
    LoopResult,
    Status,
    Task,
)
from plugins.agent_orchestration.loop_engine.loop_core.resources import (
    DecisionFixture,
    ResourceStore,
)
from plugins.agent_orchestration.loop_engine.loop_core.simulation import (
    build_scenario,
    run_linear,
)

__all__ = [
    "DecisionFixture",
    "IterationSnapshot",
    "LoopController",
    "LoopResult",
    "ResourceStore",
    "Status",
    "Task",
    "TaskGraph",
    "build_scenario",
    "export_controller_checkpoint",
    "restore_controller_checkpoint",
    "run_linear",
]
