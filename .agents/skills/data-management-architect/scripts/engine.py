"""Unified Data Management Engine — Local Skill Interface.

Re-exports and wraps DataManagementEngine and Medallion models from
``harness.services.data_management`` for direct consumption by skill users,
agents, and scripts without requiring raw package navigation.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure harness is on sys.path if invoked from the skill directory
_src_dir = Path(__file__).resolve().parents[4] / "src"
if _src_dir.exists() and str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from harness.services.data_management import (
    DataManagementEngine,
    MedallionPipelineConfig,
    MedallionPipelineResult,
    DATA_MANAGEMENT_SERVICE_KEY,
)

__all__ = [
    "DataManagementEngine",
    "MedallionPipelineConfig",
    "MedallionPipelineResult",
    "DATA_MANAGEMENT_SERVICE_KEY",
]
