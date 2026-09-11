#!/usr/bin/env python3
"""Context Anti-Rot Sync CLI — thin headless adapter for codebase context hygiene & synchronization.

Deepened architecture:
- Thin CLI adapter delegating to context_sync_engine.ContextSyncEngine
- Composite 'run' subcommand executing complete end-to-end workflow (audit, clean, sync, lint) in one atomic call
- Retains 100% backward compatibility for granular subcommands (audit, clean, sync, lint)
- Default-to-file JSON output via --output (Rule 4)
- UTF-8 standard stream reconfigure on Windows (Rule 23)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Import core domain engine and entities
try:
    from context_sync_engine import (
        AuditResult,
        CleanResult,
        ContextSyncEngine,
        ContextSyncExecutionReport,
        ContextViolation,
        LintCheckResult,
        SyncResult,
        SyncTargetRecord,
        WorkspaceLintReport,
    )
except ImportError:
    from .context_sync_engine import (  # type: ignore
        AuditResult,
        CleanResult,
        ContextSyncEngine,
        ContextSyncExecutionReport,
        ContextViolation,
        LintCheckResult,
        SyncResult,
        SyncTargetRecord,
        WorkspaceLintReport,
    )


def write_output(data: Any, output_path: str | Path) -> None:
    """Writes JSON payload to output file destination (Rule 4)."""
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Success! Output written to: {out}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Context Anti-Rot Sync CLI — automated codebase context hygiene and synchronization."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: run (composite end-to-end execution)
    p_run = subparsers.add_parser("run", help="Execute complete end-to-end context hygiene, sync & lint cycle.")
    p_run.add_argument("--target", default="AGENTS.md", help="Primary instruction file to audit and sync.")
    p_run.add_argument("--targets", nargs="*", default=None, help="Optional secondary target files.")
    p_run.add_argument("--clean-output", default=None, help="Optional output path to write cleaned target file.")
    p_run.add_argument("--root", default=None, help="Root directory to scan for workspace linting.")
    p_run.add_argument("--strict-lint", action="store_true", default=False, help="Fail run if any workspace skill has frontmatter lint issues.")
    p_run.add_argument("--output", required=True, help="Output JSON execution report destination.")

    # Subcommand: audit
    p_audit = subparsers.add_parser("audit", help="Audit an instruction file for bloat and lint leakage.")
    p_audit.add_argument("--target", default="AGENTS.md", help="Path to instruction file to audit.")
    p_audit.add_argument("--max-lines", type=int, default=150, help="Maximum line budget allowed.")
    p_audit.add_argument("--output", required=True, help="Output JSON report destination.")

    # Subcommand: clean
    p_clean = subparsers.add_parser("clean", help="Clean redundant whitespace and format instruction file.")
    p_clean.add_argument("--target", default="AGENTS.md", help="Path to instruction file to clean.")
    p_clean.add_argument("--output", required=True, help="Cleaned output destination.")

    # Subcommand: sync
    p_sync = subparsers.add_parser("sync", help="Synchronize canonical manifest rules to derived targets.")
    p_sync.add_argument("--source", default="AGENTS.md", help="Source primary manifest file.")
    p_sync.add_argument("--targets", nargs="*", default=None, help="Optional secondary target files.")
    p_sync.add_argument("--output", required=True, help="Output synchronization report destination.")

    # Subcommand: lint
    p_lint = subparsers.add_parser("lint", help="Run automated anti-rot lint verification.")
    p_lint.add_argument("--root", default=None, help="Root directory to scan.")
    p_lint.add_argument("--output", required=True, help="Output lint report destination.")

    args = parser.parse_args()
    engine = ContextSyncEngine()

    try:
        if args.command == "run":
            report = engine.execute_pipeline(
                target_file=args.target,
                sync_targets=args.targets,
                scan_root=args.root,
                clean_output=args.clean_output,
                strict_lint=args.strict_lint,
            )
            write_output(report.to_dict(), args.output)
            if not report.success:
                sys.exit(1)

        elif args.command == "audit":
            res = engine.audit_file(args.target, max_lines=args.max_lines)
            write_output(res.to_dict(), args.output)
            if not res.passed:
                sys.exit(1)

        elif args.command == "clean":
            res_clean = engine.clean_file(args.target, args.output)
            print(f"Success! Cleaned {res_clean.original_lines} -> {res_clean.cleaned_lines} lines to: {args.output}")

        elif args.command == "sync":
            res_sync = engine.sync_projections(args.source, args.targets)
            write_output(res_sync.to_dict(), args.output)

        elif args.command == "lint":
            res_lint = engine.lint_workspace(args.root)
            write_output(res_lint.to_dict(), args.output)
            if not res_lint.all_passed:
                sys.exit(1)

        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error executing context_sync_cli {args.command}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
