"""Multi-command CLI helper for architecture-deepening-workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

try:
    from .deepen_ops import cmd_push, cmd_verify
except ImportError:
    from deepen_ops import cmd_push, cmd_verify

# Windows UTF-8 Stream Codec Entrypoint Invariant (Rule 23)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def cmd_scan(args: argparse.Namespace) -> int:
    """Scan repository for monolithic files exceeding line threshold."""
    root = Path(args.root).resolve()
    threshold = args.threshold
    ignore_dirs = {".git", "node_modules", ".venv", "__pycache__", "gods_eye_view", ".gemini"}

    hotspots: list[dict[str, Any]] = []
    for base in [root / "src", root / "plugins"]:
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            if any(ign in p.parts for ign in ignore_dirs):
                continue
            if p.name == "__init__.py" and not args.include_facades:
                continue
            try:
                lines = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
                if lines > threshold:
                    hotspots.append({
                        "path": str(p.relative_to(root)).replace("\\", "/"),
                        "lines": lines,
                        "excess": lines - threshold,
                    })
            except Exception:
                pass

    hotspots.sort(key=lambda x: x["lines"], reverse=True)
    result = {"status": "ok", "threshold": threshold, "total_hotspots": len(hotspots), "hotspots": hotspots}

    if args.output:
        out_p = Path(args.output).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Success! Scan results written to: {out_p}")
    else:
        print(f"Found {len(hotspots)} files > {threshold} lines:")
        for h in hotspots[:15]:
            print(f"  {h['lines']:>4} lines | {h['path']}")
    return 0


def cmd_check_lines(args: argparse.Namespace) -> int:
    """Validate that every python file in a directory does not exceed max lines (Rule 11)."""
    target_dir = Path(args.dir).resolve()
    if not target_dir.exists():
        print(f"Error: Directory not found: {target_dir}", file=sys.stderr)
        return 1

    max_lines = args.max_lines
    violations: list[dict[str, Any]] = []
    passed_files: list[dict[str, Any]] = []

    for p in sorted(target_dir.glob("*.py")):
        lines = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
        entry = {"file": p.name, "lines": lines, "max_lines": max_lines}
        if lines > max_lines:
            violations.append(entry)
        else:
            passed_files.append(entry)

    all_passed = len(violations) == 0
    result = {
        "status": "ok" if all_passed else "failed",
        "passed": all_passed,
        "max_lines": max_lines,
        "total_files": len(passed_files) + len(violations),
        "violations": violations,
        "passed_files": passed_files,
    }

    if args.output:
        out_p = Path(args.output).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Line check report written to: {out_p}")

    if all_passed:
        print(f"✓ All {len(passed_files)} files in {target_dir.name}/ are <= {max_lines} lines!")
        return 0
    else:
        print(f"✗ Rule 11 Bound Exceeded in {len(violations)} files:", file=sys.stderr)
        for v in violations:
            print(f"  {v['file']}: {v['lines']} lines > {max_lines}", file=sys.stderr)
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Architecture Deepening Cycle Orchestrator")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    p_scan = subparsers.add_parser("scan", help="Scan for monolithic hotspots > threshold lines")
    p_scan.add_argument("--root", default=".", help="Repository root path")
    p_scan.add_argument("--threshold", type=int, default=200, help="Line count threshold")
    p_scan.add_argument("--include-facades", action="store_true", help="Include __init__.py files")
    p_scan.add_argument("--output", help="Path to write JSON output")

    p_check = subparsers.add_parser("check-lines", help="Assert all submodules <= max lines (Rule 11)")
    p_check.add_argument("--dir", required=True, help="Directory containing submodules to check")
    p_check.add_argument("--max-lines", type=int, default=200, help="Maximum allowed line count")
    p_check.add_argument("--output", help="Path to write JSON output")

    p_verify = subparsers.add_parser("verify", help="Run contract pytest and ruff lint")
    p_verify.add_argument("--root", default=".", help="Repository root path")
    p_verify.add_argument("--test", required=True, help="Path to contract test file")
    p_verify.add_argument("--lint-target", help="Path to lint target directory or file")
    p_verify.add_argument("--output", help="Path to write JSON output")

    p_push = subparsers.add_parser("push", help="Stage, commit, and push cycle files with token redaction")
    p_push.add_argument("--root", default=".", help="Repository root path")
    p_push.add_argument("--cycle", type=int, required=True, help="Cycle number")
    p_push.add_argument("--message", required=True, help="Commit description")
    p_push.add_argument("--files", nargs="+", required=True, help="List of files to stage")
    p_push.add_argument("--deleted-file", help="Old monolithic file to unstage/delete")
    p_push.add_argument("--token-file", help="Path to tokens file")
    p_push.add_argument("--dry-run", action="store_true", help="Stage and commit without pushing")

    args = parser.parse_args()
    dispatch = {"scan": cmd_scan, "check-lines": cmd_check_lines, "verify": cmd_verify, "push": cmd_push}
    sys.exit(dispatch[args.subcommand](args))


if __name__ == "__main__":
    main()
