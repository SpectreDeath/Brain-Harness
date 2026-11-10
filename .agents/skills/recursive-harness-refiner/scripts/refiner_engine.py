"""CLI entrypoint script for the recursive-harness-refiner skill.

Delegates directly to the micro-kernel recursive harnessing services (Rule 49, Rule 57).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# UTF-8 stream reconfigure on Windows (Rule 23, Rule 50)
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

# Qualified imports from harness service package (Rule 57)
from harness.services.recursive_harnessing import (
    BRAIN_SURFACE,
    expected_rollouts,
    expected_sessions,
    fingerprint_dir,
    resolve_recursive_refiner,
)


def main() -> int:
    """Print budget and surface configuration."""
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    summary = {
        "k": k,
        "expected_rollouts": expected_rollouts(k),
        "expected_sessions": expected_sessions(k),
        "surface": {
            "name": BRAIN_SURFACE.name,
            "always_on": BRAIN_SURFACE.always_on,
            "max_chars": BRAIN_SURFACE.always_on_max,
            "skill_dir": BRAIN_SURFACE.skill_dir,
        },
    }
    sys.stdout.write(json.dumps(summary, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
