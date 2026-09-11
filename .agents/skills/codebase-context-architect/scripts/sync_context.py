# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""Context File Synchronizer for Multi-Vendor AI Coding Agents.

Thin CLI adapter delegating to the deep-module CodebaseContextEngine.
Maintains 100% backward compatibility for callers of sync_repository(root) and CLI flags.

Usage:
    python sync_context.py [--root <dir>] [--source <file>] [--dry-run] [--silent]
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Ensure scripts directory is on sys.path for relative engine import
_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from engine import CodebaseContextEngine, SyncResult

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def sync_repository(root: Path, source_rel: str = "AGENTS.md", dry_run: bool = False) -> tuple[bool, list[str]]:
    """Synchronize downstream context files against canonical source via CodebaseContextEngine."""
    engine = CodebaseContextEngine(root=root)
    result: SyncResult = engine.sync(source_rel=source_rel, dry_run=dry_run)
    return result.in_sync, list(result.actions)


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-Vendor Context File Synchronizer")
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument("--source", default="AGENTS.md", help="Canonical source filename")
    parser.add_argument("--dry-run", action="store_true", help="Check for drift without writing changes")
    parser.add_argument("--silent", action="store_true", help="Suppress output on success")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    engine = CodebaseContextEngine(root=root)
    result: SyncResult = engine.sync(source_rel=args.source, dry_run=args.dry_run)

    if not args.silent or not result.in_sync:
        for action in result.actions:
            stream = sys.stderr if not result.in_sync and args.dry_run else sys.stdout
            print(action, file=stream)

    if args.dry_run and not result.in_sync:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
