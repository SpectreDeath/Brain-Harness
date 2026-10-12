"""Coding Harness Calibrator commands — modular subpackage facade."""

from __future__ import annotations

from harness.commands.calibrator.brief import calibrator_brief_cli
from harness.commands.calibrator.engine_adapter import (
    CodingHarnessCalibratorEngineAdapter,
)
from harness.commands.calibrator.group import calibrator_group
from harness.commands.calibrator.recommend import calibrator_recommend_cli
from harness.commands.calibrator.repatch import calibrator_repatch_cli
from harness.commands.calibrator.resolver import get_calibrator_service
from harness.commands.calibrator.staging import calibrator_staging_cli

__all__ = [
    "CodingHarnessCalibratorEngineAdapter",
    "calibrator_brief_cli",
    "calibrator_group",
    "calibrator_recommend_cli",
    "calibrator_repatch_cli",
    "calibrator_staging_cli",
    "get_calibrator_service",
]
