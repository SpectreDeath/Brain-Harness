"""Co-located unit test contract for rea_mobile_firmware plugin."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tests.test_plugin_rea_mobile_firmware import TestReaMobileFirmwarePlugin, plugin_dir

__all__ = ["TestReaMobileFirmwarePlugin", "plugin_dir"]
