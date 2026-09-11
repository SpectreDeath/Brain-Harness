# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""Context File Linter for AI Coding Agents.

Thin CLI adapter delegating to the deep-module CodebaseContextEngine.
Maintains 100% backward compatibility for callers of run_linter(root) and CLI flags.

Usage:
    python context_linter.py [--root <dir>] [--silent] [--json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

# Ensure scripts directory is on sys.path for relative engine import
_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from engine import (
    CodebaseContextEngine,
    ContextLintReport,
    TokenBudgetCheck,
    PathIntegrityCheck,
    ScriptIntegrityCheck,
    SyncDriftCheck,
)

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def run_linter(root: Path, budgets: dict[str, int] | None = None) -> dict[str, Any]:
    """Execute complete 4-check context verification suite via CodebaseContextEngine."""
    config = {"budgets": budgets} if budgets else None
    engine = CodebaseContextEngine(root=root, config=config)
    report: ContextLintReport = engine.lint()
    return report.to_dict()


def main() -> int:
    parser = argparse.ArgumentParser(description="Codebase Context File Linter")
    parser.add_argument("--root", default=".", help="Repository root path (default: current directory)")
    parser.add_argument("--silent", action="store_true", help="Suppress output on pass; only output on error")
    parser.add_argument("--json", action="store_true", help="Format output as JSON")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    engine = CodebaseContextEngine(root=root)
    report: ContextLintReport = engine.lint()

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return 0 if report.passed else 1

    if report.passed:
        if not args.silent:
            print(f"[PASS] Context files healthy across {report.checks_count} checks at: {root}")
        return 0

    print(f"[FAIL] Context file linter detected {report.problems_count} problem(s):", file=sys.stderr)
    for p in report.problems:
        print(f"  - [{p.to_dict()['check']}] {p.message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
