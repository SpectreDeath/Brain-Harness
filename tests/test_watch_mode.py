"""Unit tests for comment trigger scanning and autonomous watch mode."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from harness.plugins.watcher import (
    CommentTrigger,
    scan_file_for_triggers,
)


@pytest.mark.unit
def test_scan_file_for_harness_triggers() -> None:
    """Test extracting # HARNESS: and // AI: triggers from code files."""
    content = '''
# Normal comment
def calculate_tax(income: float) -> float:
    # HARNESS: add validation to check income is non-negative
    rate = 0.2
    // AI: optimize rate lookup table
    return income * rate
'''
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        triggers = scan_file_for_triggers(temp_path)
        assert len(triggers) == 2
        assert "add validation" in triggers[0].instruction
        assert "optimize rate" in triggers[1].instruction
    finally:
        Path(temp_path).unlink(missing_ok=True)
