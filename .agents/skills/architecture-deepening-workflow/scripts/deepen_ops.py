"""Verification and push operations for architecture-deepening-workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


def cmd_verify(args: argparse.Namespace) -> int:
    """Run pytest contract tests and ruff linting."""
    root = Path(args.root).resolve()
    test_target = args.test
    lint_target = args.lint_target or args.test

    print(f"Running contract verification for: {test_target}")
    pytest_res = subprocess.run(
        ["pytest", test_target, "-v", "--tb=short"],
        cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    print(f"Running ruff static analysis for: {lint_target}")
    ruff_res = subprocess.run(
        ["ruff", "check", lint_target],
        cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )

    passed = pytest_res.returncode == 0 and ruff_res.returncode == 0
    result = {
        "status": "ok" if passed else "failed",
        "pytest_exit_code": pytest_res.returncode,
        "ruff_exit_code": ruff_res.returncode,
        "pytest_stdout": pytest_res.stdout,
        "ruff_stdout": ruff_res.stdout,
    }

    if args.output:
        out_p = Path(args.output).resolve()
        out_p.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Verification report written to: {out_p}")

    if passed:
        print("✓ All contract tests and ruff lint checks passed cleanly!")
        return 0
    else:
        print("✗ Verification failed:", file=sys.stderr)
        if pytest_res.returncode != 0:
            print(pytest_res.stdout, file=sys.stderr)
        if ruff_res.returncode != 0:
            print(ruff_res.stdout, file=sys.stderr)
        return 1


def cmd_push(args: argparse.Namespace) -> int:
    """Stage cycle files and push with in-memory token redaction (Rule 15)."""
    root = Path(args.root).resolve()
    token_path = Path(args.token_file or r"D:\GitHub\projects\Tokens\tokens.txt").resolve()
    if not token_path.exists():
        print(f"Error: Token file not found at {token_path}", file=sys.stderr)
        return 1

    token = token_path.read_text(encoding="utf-8", errors="ignore").strip()
    if not token:
        print("Error: Token file is empty", file=sys.stderr)
        return 1

    def redact(t: str) -> str:
        return t.replace(token, "***REDACTED***") if t else ""

    files = args.files
    if not files:
        print("Error: No files specified to stage", file=sys.stderr)
        return 1

    print(f"Staging {len(files)} cycle files...")
    subprocess.run(["git", "add"] + files, cwd=root, check=True)

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
    if push_res.stdout:
        print(redact(push_res.stdout).strip())
    if push_res.stderr:
        print(redact(push_res.stderr).strip())

    if push_res.returncode == 0:
        print(f"✓ Successfully pushed Cycle {args.cycle} to GitHub!")
        return 0
    else:
        print(f"✗ Push failed with return code {push_res.returncode}", file=sys.stderr)
        return push_res.returncode
