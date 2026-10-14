"""Multi-command CLI orchestrator for architecture-deepening-workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

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
                    hotspots.append({"path": str(p.relative_to(root)).replace("\\", "/"), "lines": lines, "excess": lines - threshold})
            except Exception:
                pass

    hotspots.sort(key=lambda x: x["lines"], reverse=True)
    result = {"status": "ok", "threshold": threshold, "total_hotspots": len(hotspots), "hotspots": hotspots}

    if args.output:
        Path(args.output).resolve().parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).resolve().write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Success! Scan results written to: {args.output}")
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
        (violations if lines > max_lines else passed_files).append({"file": p.name, "lines": lines, "max_lines": max_lines})

    all_passed = len(violations) == 0
    result = {"status": "ok" if all_passed else "failed", "passed": all_passed, "max_lines": max_lines, "violations": violations, "passed_files": passed_files}

    if args.output:
        Path(args.output).resolve().parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).resolve().write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Line check report written to: {args.output}")

    if all_passed:
        print(f"✓ All {len(passed_files)} files in {target_dir.name}/ are <= {max_lines} lines!")
        return 0
    print(f"✗ Rule 11 Bound Exceeded in {len(violations)} files:", file=sys.stderr)
    for v in violations:
        print(f"  {v['file']}: {v['lines']} lines > {max_lines}", file=sys.stderr)
    return 1


def cmd_verify(args: argparse.Namespace) -> int:
    """Run pytest contract tests and ruff linting."""
    root = Path(args.root).resolve()
    test_target = args.test
    lint_target = args.lint_target or args.test

    print(f"Running contract verification for: {test_target}")
    pytest_res = subprocess.run(["pytest", test_target, "-v", "--tb=short"], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(f"Running ruff static analysis for: {lint_target}")
    ruff_res = subprocess.run(["ruff", "check", lint_target], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")

    passed = pytest_res.returncode == 0 and ruff_res.returncode == 0
    result = {"status": "ok" if passed else "failed", "pytest_code": pytest_res.returncode, "ruff_code": ruff_res.returncode}

    if args.output:
        Path(args.output).resolve().write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Verification report written to: {args.output}")

    if passed:
        print("✓ All contract tests and ruff lint checks passed cleanly!")
        return 0
    print("✗ Verification failed:", file=sys.stderr)
    for res in (pytest_res, ruff_res):
        if res.returncode != 0:
            print(res.stdout, file=sys.stderr)
    return 1


def cmd_push(args: argparse.Namespace) -> int:
    """Stage cycle files and push with in-memory token redaction (Rule 15)."""
    root = Path(args.root).resolve()
    token_path = Path(args.token_file or r"D:\GitHub\projects\Tokens\tokens.txt").resolve()
    if not token_path.exists():
        print(f"Error: Token file not found at {token_path}", file=sys.stderr)
        return 1

    token = token_path.read_text(encoding="utf-8", errors="ignore").strip()
    if not token or not args.files:
        print("Error: Empty token or no files specified", file=sys.stderr)
        return 1

    redact = lambda t: t.replace(token, "***REDACTED***") if t else ""
    print(f"Staging {len(args.files)} cycle files...")
    subprocess.run(["git", "add"] + args.files, cwd=root, check=True)
    if args.deleted_file:
        subprocess.run(["git", "rm", "--cached", args.deleted_file], cwd=root, check=False)

    commit_msg = f"refactor(cycle-{args.cycle}): {args.message}"
    print(f"Committing: {commit_msg}")
    commit_res = subprocess.run(["git", "commit", "-m", commit_msg], cwd=root, capture_output=True, text=True)
    print(commit_res.stdout.strip())

    if args.dry_run:
        print("✓ Dry run enabled: skipped remote git push.")
        return 0

    auth_url = f"https://{token}@github.com/SpectreDeath/Brain-Harness.git"
    print("Pushing to remote origin main...")
    push_res = subprocess.run(["git", "push", auth_url, "main"], cwd=root, capture_output=True, text=True)
    for out in (push_res.stdout, push_res.stderr):
        if out:
            print(redact(out).strip())
    return push_res.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Architecture Deepening Cycle Orchestrator")
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_scan = sub.add_parser("scan")
    p_scan.add_argument("--root", default=".")
    p_scan.add_argument("--threshold", type=int, default=200)
    p_scan.add_argument("--include-facades", action="store_true")
    p_scan.add_argument("--output")

    p_chk = sub.add_parser("check-lines")
    p_chk.add_argument("--dir", required=True)
    p_chk.add_argument("--max-lines", type=int, default=200)
    p_chk.add_argument("--output")

    p_ver = sub.add_parser("verify")
    p_ver.add_argument("--root", default=".")
    p_ver.add_argument("--test", required=True)
    p_ver.add_argument("--lint-target")
    p_ver.add_argument("--output")

    p_push = sub.add_parser("push")
    p_push.add_argument("--root", default=".")
    p_push.add_argument("--cycle", type=int, required=True)
    p_push.add_argument("--message", required=True)
    p_push.add_argument("--files", nargs="+", required=True)
    p_push.add_argument("--deleted-file")
    p_push.add_argument("--token-file")
    p_push.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    dispatch = {"scan": cmd_scan, "check-lines": cmd_check_lines, "verify": cmd_verify, "push": cmd_push}
    sys.exit(dispatch[args.subcommand](args))


if __name__ == "__main__":
    main()
